import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  BookOpen,
  Layers,
  Terminal,
  Play,
  RotateCcw,
  CheckCircle,
  FileText
} from "lucide-react";
import apiClient from "../services/api";
import { useBuildStore } from "../stores/buildStore";
import SetupChecklist from "../components/project/SetupChecklist";
import BuildStats from "../components/build/BuildStats";
import BuildProgress from "../components/build/BuildProgress";
import SprintAccordion from "../components/build/SprintAccordion";
import BuildLog from "../components/build/BuildLog";

type Tab = "overview" | "documents" | "build" | "setup";

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);
  const [setupSteps, setSetupSteps] = useState<any[]>([]);
  const [envTemplate, setEnvTemplate] = useState<string>("");
  const [isRegeneratingDoc, setIsRegeneratingDoc] = useState<string | null>(null);

  const {
    project,
    sprints,
    logs,
    status,
    stats,
    fetchBuildStatus,
    startBuild,
    connectLogStream,
    disconnectLogStream
  } = useBuildStore();

  useEffect(() => {
    if (!projectId) return;

    fetchBuildStatus(projectId);

    // Fetch setup checklist & env template
    apiClient.get(`/api/v1/projects/${projectId}/setup-guide`)
      .then((res) => setSetupSteps(res.data.steps || []))
      .catch(console.error);

    apiClient.get(`/api/v1/projects/${projectId}/env-template`)
      .then((res) => setEnvTemplate(res.data.env_template || ""))
      .catch(console.error);

    const interval = setInterval(() => {
      fetchBuildStatus(projectId);
    }, 5000);

    return () => {
      clearInterval(interval);
    };
  }, [projectId, fetchBuildStatus]);

  // Connect/disconnect log stream only when activeTab is "build"
  useEffect(() => {
    if (!projectId) return;
    if (activeTab === "build") {
      connectLogStream(projectId);
    } else {
      disconnectLogStream();
    }
    return () => disconnectLogStream();
  }, [projectId, activeTab, connectLogStream, disconnectLogStream]);

  if (!project) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-400 font-mono">
        Loading project details...
      </div>
    );
  }

  const handleRegenerateDoc = async (docType: string) => {
    if (!projectId) return;
    setIsRegeneratingDoc(docType);
    try {
      // Re-trigger document generation
      await apiClient.post(`/api/v1/projects/${projectId}/generate-docs`);
      await fetchBuildStatus(projectId);
      if (selectedDoc && selectedDoc.doc_type === docType) {
        // Refresh selected doc
        const updated = project.documents?.find((d: any) => d.doc_type === docType);
        if (updated) setSelectedDoc(updated);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsRegeneratingDoc(null);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "complete":
        return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      case "building":
      case "in_progress":
        return "bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse";
      case "paused":
        return "bg-slate-800 text-slate-400 border border-slate-700/60";
      default:
        return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
    }
  };

  const overallProgress = stats.totalTasks > 0 ? (stats.completedTasks / stats.totalTasks) * 100 : 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <Link
            to="/approvals"
            className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors font-mono mb-2"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>BACK TO PROJECTS</span>
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">{project.name}</h1>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold font-mono ${getStatusBadgeClass(project.status)}`}>
              {project.status.toUpperCase()}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">{project.description}</p>
          
          <div className="flex flex-wrap gap-2 mt-3">
            <span className="bg-slate-850 border border-slate-800 text-slate-400 text-xs px-2.5 py-1 rounded font-mono">
              Industry: {project.industry}
            </span>
            {Array.isArray(project.tech_stack) && project.tech_stack.map((tech: string, i: number) => (
              <span key={i} className="bg-blue-500/5 border border-blue-500/10 text-blue-400 text-xs px-2.5 py-1 rounded font-mono">
                {tech}
              </span>
            ))}
          </div>
        </div>

        {project.status !== "complete" && projectId && (
          <button
            onClick={() => startBuild(projectId)}
            disabled={project.status === "building"}
            className="flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition-all border border-blue-500/20 shadow disabled:opacity-50 disabled:cursor-not-allowed font-mono"
          >
            <Play className="w-4 h-4" />
            <span>{project.status === "paused" ? "RESUME BUILD" : "START PIPELINE"}</span>
          </button>
        )}
      </div>

      {/* Tabs list */}
      <div className="flex space-x-1 border-b border-slate-800">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-4 py-2 text-sm font-semibold font-mono border-b-2 transition-all ${
            activeTab === "overview"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab("documents")}
          className={`px-4 py-2 text-sm font-semibold font-mono border-b-2 transition-all ${
            activeTab === "documents"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Documents
        </button>
        <button
          onClick={() => setActiveTab("build")}
          className={`px-4 py-2 text-sm font-semibold font-mono border-b-2 transition-all ${
            activeTab === "build"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Build Progress
        </button>
        {project.status === "complete" && (
          <button
            onClick={() => setActiveTab("setup")}
            className={`px-4 py-2 text-sm font-semibold font-mono border-b-2 transition-all ${
              activeTab === "setup"
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Setup Guide
          </button>
        )}
      </div>

      {/* Tab Panels */}
      <div className="mt-4">
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Solution summary */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                <h3 className="text-base font-semibold text-slate-200 font-mono">Solution Blueprint</h3>
                <p className="text-sm text-slate-300 leading-relaxed">{project.description}</p>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800">
                  <div>
                    <span className="text-xs text-slate-500 font-mono uppercase">Maturity Target</span>
                    <p className="text-sm font-semibold text-slate-300 mt-1 uppercase font-mono">{project.maturity_level}</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 font-mono uppercase">Generated Path</span>
                    <p className="text-sm font-semibold text-slate-300 mt-1 break-all font-mono">{project.project_dir || "/tmp"}</p>
                  </div>
                </div>
              </div>

              {/* Build statistics */}
              <BuildStats stats={stats} />
            </div>

            {/* Timeline */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
              <h3 className="text-base font-semibold text-slate-200 font-mono">Project Timeline</h3>
              <div className="relative border-l border-slate-800 ml-3 space-y-6 pt-2">
                <div className="relative pl-6">
                  <span className="absolute -left-[6.5px] top-1 w-3 h-3 rounded-full bg-emerald-500 border border-slate-950"></span>
                  <p className="text-xs font-semibold text-slate-400 font-mono">Created</p>
                  <p className="text-xs text-slate-500 mt-0.5">{new Date(project.created_at).toLocaleString()}</p>
                </div>
                <div className="relative pl-6">
                  <span className={`absolute -left-[6.5px] top-1 w-3 h-3 rounded-full border border-slate-950 ${
                    project.documents && project.documents.length > 0 ? "bg-emerald-500" : "bg-slate-800"
                  }`}></span>
                  <p className="text-xs font-semibold text-slate-400 font-mono">Documents Generated</p>
                </div>
                <div className="relative pl-6">
                  <span className={`absolute -left-[6.5px] top-1 w-3 h-3 rounded-full border border-slate-950 ${
                    project.status !== "doc_generation" && project.status !== "doc_review" ? "bg-emerald-500" : "bg-slate-800"
                  }`}></span>
                  <p className="text-xs font-semibold text-slate-400 font-mono">Build Pipeline Initiated</p>
                </div>
                <div className="relative pl-6">
                  <span className={`absolute -left-[6.5px] top-1 w-3 h-3 rounded-full border border-slate-950 ${
                    project.status === "complete" ? "bg-emerald-500" : "bg-slate-800"
                  }`}></span>
                  <p className="text-xs font-semibold text-slate-400 font-mono">Deployment Ready</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "documents" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* List */}
            <div className="space-y-3">
              <h3 className="text-base font-semibold text-slate-200 font-mono mb-2">Technical Artifacts</h3>
              {project.documents && project.documents.length > 0 ? (
                project.documents.map((doc: any) => {
                  const isSelected = selectedDoc?.id === doc.id;
                  return (
                    <button
                      key={doc.id}
                      onClick={() => setSelectedDoc(doc)}
                      className={`w-full text-left p-4 rounded-xl border transition-all flex items-center justify-between ${
                        isSelected
                          ? "bg-blue-500/5 border-blue-500/20 text-blue-400"
                          : "bg-slate-900 border-slate-850 text-slate-300 hover:bg-slate-850"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-semibold">{doc.title}</p>
                          <p className="text-xs text-slate-500 mt-0.5 uppercase font-mono">{doc.doc_type}</p>
                        </div>
                      </div>
                      <span className="text-xs text-slate-500 font-mono">v{doc.version || 1}</span>
                    </button>
                  );
                })
              ) : (
                <p className="text-sm text-slate-500 py-4">No documents available.</p>
              )}
            </div>

            {/* Viewer */}
            <div className="lg:col-span-2">
              {selectedDoc ? (
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg flex flex-col h-[600px]">
                  <div className="bg-slate-800/80 px-6 py-4 flex items-center justify-between border-b border-slate-800">
                    <div>
                      <h4 className="text-sm font-bold text-slate-200">{selectedDoc.title}</h4>
                      <p className="text-xs text-slate-500 uppercase tracking-wider font-mono mt-0.5">{selectedDoc.doc_type}</p>
                    </div>
                    <button
                      onClick={() => handleRegenerateDoc(selectedDoc.doc_type)}
                      disabled={isRegeneratingDoc === selectedDoc.doc_type}
                      className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-650 disabled:opacity-50 text-xs font-semibold rounded border border-slate-600 font-mono transition-colors text-slate-200"
                    >
                      <RotateCcw className={`w-3.5 h-3.5 ${isRegeneratingDoc === selectedDoc.doc_type ? 'animate-spin' : ''}`} />
                      <span>REGENERATE</span>
                    </button>
                  </div>
                  <div className="flex-1 p-6 overflow-y-auto font-sans text-sm text-slate-300 bg-slate-950/60 leading-relaxed whitespace-pre-wrap select-text">
                    {selectedDoc.content}
                  </div>
                </div>
              ) : (
                <div className="bg-slate-900 border border-slate-850 rounded-xl h-[400px] flex flex-col items-center justify-center text-slate-500 font-mono">
                  <BookOpen className="w-10 h-10 text-slate-600 mb-3" />
                  <span>Select a document to display the content.</span>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "build" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <BuildProgress progress={overallProgress} />
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-center">
                <span className="text-xs text-slate-500 font-mono uppercase">Build Summary</span>
                <div className="flex items-baseline space-x-2 mt-2">
                  <span className="text-2xl font-bold font-mono text-slate-100">{stats.completedTasks}</span>
                  <span className="text-slate-500 text-sm">/ {stats.totalTasks} Tasks Completed</span>
                </div>
                <div className="mt-4 flex items-center space-x-2 text-xs text-slate-400">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>All tasks built successfully on Claude Pipeline.</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-base font-semibold text-slate-200 font-mono">Sprints & Tasks</h3>
                <SprintAccordion sprints={sprints} />
              </div>
              <div className="space-y-4">
                <h3 className="text-base font-semibold text-slate-200 font-mono">Real-time Activity Logs</h3>
                <BuildLog logs={logs} isConnected={true} />
              </div>
            </div>
          </div>
        )}

        {activeTab === "setup" && (
          <div className="max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-base font-bold text-slate-200 font-mono mb-4">Post-Build Setup Guide</h3>
            <SetupChecklist steps={setupSteps} envTemplate={envTemplate} />
          </div>
        )}
      </div>
    </div>
  );
}
