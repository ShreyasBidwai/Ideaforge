import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  BookOpen,
  Layers,
  Terminal,
  Play,
  RotateCcw,
  CheckCircle,
  FileText,
  Loader2,
  AlertTriangle,
  Trash2
} from "lucide-react";
import apiClient from "../services/api";
import { useBuildStore } from "../stores/buildStore";
import SetupChecklist from "../components/project/SetupChecklist";
import BuildStats from "../components/build/BuildStats";
import BuildProgress from "../components/build/BuildProgress";
import SprintAccordion from "../components/build/SprintAccordion";
import BuildLog from "../components/build/BuildLog";
import DocumentViewer from "../components/project/DocumentViewer";
import DocumentEditor from "../components/project/DocumentEditor";
import SprintReview from "../components/project/SprintReview";
import DocGenerationProgress from "../components/project/DocGenerationProgress";
import FileBrowser from "../components/project/FileBrowser";
import { useRunStore } from "../stores/runStore";
import SetupGate from "../components/run/SetupGate";
import RunPanel from "../components/run/RunPanel";
import RunLogs from "../components/run/RunLogs";

type Tab = "overview" | "documents" | "build" | "setup" | "code" | "run";

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);
  const [setupSteps, setSetupSteps] = useState<any[]>([]);
  const [envTemplate, setEnvTemplate] = useState<string>("");
  const [isRegeneratingDoc, setIsRegeneratingDoc] = useState<string | null>(null);
  const [editingDocId, setEditingDocId] = useState<string | null>(null);
  const [expandedDocs, setExpandedDocs] = useState<Record<string, boolean>>({});

  const {
    project,
    sprints,
    logs,
    status,
    stats,
    fetchBuildStatus,
    startBuild,
    retryFailed,
    connectLogStream,
    disconnectLogStream,
    docGenerationProgress,
    sprintGenerationProgress,
    generateDocsStream,
    generateSprintsStream,
    cancelDocGeneration,
    cancelSprintGeneration
  } = useBuildStore();

  const runStore = useRunStore();

  useEffect(() => {
    if (!projectId) return;
    runStore.fetchManifest(projectId);
  }, [projectId, runStore.fetchManifest]);

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

  useEffect(() => {
    if (projectId && project?.status === "doc_generation" && !docGenerationProgress) {
      generateDocsStream(projectId);
    }
  }, [projectId, project?.status, docGenerationProgress, generateDocsStream]);

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

  const handleRetryDocGeneration = async () => {
    if (!projectId) return;
    try {
      await generateDocsStream(projectId);
    } catch (e) {
      console.error("Failed to retry doc generation:", e);
    }
  };

  const toggleDoc = (docId: string) => {
    setExpandedDocs((prev) => ({ ...prev, [docId]: !prev[docId] }));
  };

  const handleApproveDoc = async (docId: string) => {
    if (!projectId) return;
    try {
      await apiClient.post(`/api/v1/projects/${projectId}/documents/${docId}/approve`);
      await fetchBuildStatus(projectId);
      setEditingDocId(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveDoc = async (docId: string, content: string) => {
    if (!projectId) return;
    try {
      await apiClient.patch(`/api/v1/projects/${projectId}/documents/${docId}`, { content });
      await fetchBuildStatus(projectId);
    } catch (e) {
      console.error(e);
    }
  };

  const handleApproveAllDocs = async () => {
    if (!projectId) return;
    try {
      await apiClient.post(`/api/v1/projects/${projectId}/documents/approve-all`);
      await fetchBuildStatus(projectId);
    } catch (e) {
      console.error(e);
    }
  };

  const handleEditTaskPrompt = async (taskId: string, prompt: string) => {
    if (!projectId) return;
    try {
      await apiClient.patch(`/api/v1/tasks/${taskId}/prompt`, { prompt });
      await fetchBuildStatus(projectId);
    } catch (e) {
      console.error(e);
    }
  };

  const handleApproveEverythingAndBuild = async () => {
    if (!projectId) return;
    try {
      // 1. Approve all documents first
      await apiClient.post(`/api/v1/projects/${projectId}/documents/approve-all`);
      
      // 2. Fetch latest status to check sprints
      await fetchBuildStatus(projectId);
      
      // 3. If sprints are not generated, trigger sprint generation stream and wait for it
      if (!sprints || sprints.length === 0) {
        await generateSprintsStream(projectId);
        // Refresh again to ensure we have the new sprints
        await fetchBuildStatus(projectId);
      }
      
      // 4. Start the build
      await apiClient.post(`/api/v1/projects/${projectId}/approve-and-build`);
      await fetchBuildStatus(projectId);
      setActiveTab("build");
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteProject = async () => {
    if (!projectId) return;
    if (
      !window.confirm(
        "Are you sure you want to delete this project? This will permanently delete all sprints, tasks, files, and build logs."
      )
    ) {
      return;
    }
    try {
      await apiClient.delete(`/api/v1/projects/${projectId}`);
      navigate("/approvals");
    } catch (e) {
      console.error(e);
      alert("Error deleting project. Please try again.");
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
      case "doc_generation_failed":
        return "bg-red-500/10 text-red-400 border border-red-500/20";
      default:
        return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
    }
  };

  const overallProgress = stats.totalTasks > 0 ? (stats.completedTasks / stats.totalTasks) * 100 : 0;
  const allDocsApproved = Array.isArray(project.documents) &&
    project.documents.length > 0 &&
    project.documents.every((d: any) => d.status === "approved");

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

        <div className="flex items-center gap-3">
          {projectId && (
            <button
              onClick={handleDeleteProject}
              className="flex items-center space-x-2 px-5 py-2.5 bg-red-950/30 hover:bg-red-900/40 text-red-400 hover:text-red-300 rounded-lg text-sm font-semibold transition-all border border-red-500/20 shadow font-mono"
            >
              <Trash2 className="w-4 h-4" />
              <span>DELETE PROJECT</span>
            </button>
          )}

          {((project.status === "paused" || project.status === "building") || 
            (project.status === "failed" && sprints && sprints.length > 0)) && projectId && (
            <button
              onClick={() => {
                if (project.status === "failed") {
                  retryFailed(projectId);
                } else {
                  startBuild(projectId);
                }
              }}
              disabled={project.status === "building"}
              className="flex items-center space-x-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition-all border border-blue-500/20 shadow disabled:opacity-50 disabled:cursor-not-allowed font-mono"
            >
              <Play className="w-4 h-4" />
              <span>{project.status === "paused" || project.status === "failed" ? "RESUME BUILD" : "START PIPELINE"}</span>
            </button>
          )}
        </div>
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
        <button
          onClick={() => setActiveTab("code")}
          className={`px-4 py-2 text-sm font-semibold font-mono border-b-2 transition-all ${
            activeTab === "code"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Code
        </button>
        <button
          onClick={() => setActiveTab("run")}
          className={`px-4 py-2 text-sm font-semibold font-mono border-b-2 transition-all ${
            activeTab === "run"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Run
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
          <div className="space-y-6">
            {project.status === "doc_generation_failed" ? (
              <div className="bg-slate-900/60 border border-red-500/20 rounded-2xl p-8 flex flex-col items-center justify-center min-h-[300px] text-center space-y-4">
                <div className="p-3.5 bg-red-500/10 text-red-400 rounded-full">
                  <AlertTriangle className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-bold text-white font-mono uppercase tracking-wider">Document Generation Failed</h3>
                <p className="text-sm text-slate-400 max-w-md leading-relaxed">
                  An error occurred while generating the project blueprints (AI provider rate limits or daily requests quota exceeded).
                </p>
                <button
                  onClick={handleRetryDocGeneration}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition-all border border-blue-500/20 shadow shadow-blue-550/20 font-mono"
                >
                  RETRY DOCUMENT GENERATION
                </button>
              </div>
            ) : project.status === "doc_generation" || docGenerationProgress ? (
              <DocGenerationProgress
                completedDocs={docGenerationProgress?.completedDocs || []}
                currentDoc={docGenerationProgress?.currentDoc || null}
                onCancel={() => projectId && cancelDocGeneration(projectId)}
              />
            ) : project.status === "doc_review" ? (
              <div className="space-y-6">
                {/* Header Actions */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white font-mono">Document Review</h3>
                    <p className="text-sm text-slate-400">All documents must be approved before you can start the build.</p>
                  </div>
                  <div className="flex space-x-3 w-full sm:w-auto">
                    <button
                      onClick={handleApproveAllDocs}
                      className="flex-1 sm:flex-initial px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded-lg text-sm transition font-mono border border-slate-700"
                    >
                      APPROVE ALL DOCUMENTS
                    </button>
                    <button
                      onClick={handleApproveEverythingAndBuild}
                      disabled={sprintGenerationProgress !== null}
                      className="flex-1 sm:flex-initial px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium rounded-lg text-sm transition-all border border-indigo-500/20 shadow-lg shadow-indigo-600/20 font-mono uppercase"
                    >
                      BUILD APP
                    </button>
                  </div>
                </div>

                {/* Sprints breakdown if all docs approved */}
                {allDocsApproved && sprints && sprints.length > 0 && (
                  <div className="bg-slate-900/30 p-6 rounded-2xl border border-slate-800 space-y-4">
                    {sprintGenerationProgress ? (
                      <div className="flex flex-col items-center justify-center min-h-[200px] text-center space-y-3">
                        <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
                        <h4 className="text-base font-bold text-white uppercase font-mono">
                          {sprintGenerationProgress.status === "analyzing" ? "Analyzing Documentation" : "Regenerating Tasks"}
                        </h4>
                        <p className="text-sm text-slate-400">{sprintGenerationProgress.message}</p>
                        <button
                          onClick={() => projectId && cancelSprintGeneration(projectId)}
                          className="px-4 py-1.5 rounded-full text-xs font-semibold bg-rose-500/10 border border-rose-500/25 text-rose-400 hover:bg-rose-500/20 active:bg-rose-500/30 transition-all cursor-pointer font-mono uppercase"
                        >
                          Terminate
                        </button>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                          <h3 className="text-lg font-bold text-white font-mono">Sprint Review</h3>
                          <button
                            onClick={() => generateSprintsStream(projectId!)}
                            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition border border-slate-700 font-mono"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                            REGENERATE SPRINTS
                          </button>
                        </div>
                        <SprintReview
                          sprints={sprints}
                          onEditPrompt={handleEditTaskPrompt}
                          onApproveAndBuild={handleApproveEverythingAndBuild}
                        />
                      </>
                    )}
                  </div>
                )}

                {allDocsApproved && (!sprints || sprints.length === 0) && (
                  <div className="bg-slate-900/30 p-6 rounded-2xl border border-slate-800 space-y-4 flex flex-col items-center justify-center min-h-[200px]">
                    {sprintGenerationProgress ? (
                      <div className="text-center space-y-3">
                        <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
                        <h4 className="text-base font-bold text-white uppercase font-mono">
                          {sprintGenerationProgress.status === "analyzing" ? "Analyzing Documentation" : "Generating Tasks"}
                        </h4>
                        <p className="text-sm text-slate-400">{sprintGenerationProgress.message}</p>
                        <button
                          onClick={() => projectId && cancelSprintGeneration(projectId)}
                          className="px-4 py-1.5 rounded-full text-xs font-semibold bg-rose-500/10 border border-rose-500/25 text-rose-400 hover:bg-rose-500/20 active:bg-rose-500/30 transition-all cursor-pointer font-mono uppercase mt-2"
                        >
                          Terminate
                        </button>
                      </div>
                    ) : (
                      <div className="text-center space-y-4">
                        <p className="text-sm text-slate-400">Documents approved! Now, generate the sprint breakdown and task prompts.</p>
                        <button
                          onClick={() => generateSprintsStream(projectId!)}
                          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition-all border border-blue-500/20 font-mono shadow-md"
                        >
                          GENERATE SPRINT PLAN & TASKS
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Document Accordions */}
                <div className="space-y-4">
                  {project.documents?.map((doc: any) => {
                    const isExpanded = !!expandedDocs[doc.id];
                    const isEditing = editingDocId === doc.id;
                    const docStatusClass = doc.status === "approved"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20";

                    return (
                      <div key={doc.id} className="border border-slate-800 bg-slate-900/50 rounded-xl overflow-hidden">
                        {/* Accordion Header */}
                        <div
                          onClick={() => toggleDoc(doc.id)}
                          className="w-full flex items-center justify-between px-6 py-4 cursor-pointer hover:bg-slate-900 transition text-left"
                        >
                          <div className="flex items-center space-x-3">
                            <FileText className="w-5 h-5 text-slate-400" />
                            <span className="text-base font-bold text-white">{doc.title}</span>
                            <span className={`px-2 py-0.5 text-xs font-semibold rounded-full capitalize font-mono ${docStatusClass}`}>
                              {doc.status}
                            </span>
                          </div>

                          <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => {
                                setEditingDocId(doc.id);
                                if (!isExpanded) toggleDoc(doc.id);
                              }}
                              className="px-3 py-1.5 text-xs bg-slate-850 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-md transition font-mono"
                            >
                              REVIEW & EDIT
                            </button>
                            <button
                              onClick={() => handleRegenerateDoc(doc.doc_type)}
                              disabled={isRegeneratingDoc === doc.doc_type}
                              className="px-3 py-1.5 text-xs bg-slate-855 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-md transition flex items-center space-x-1 font-mono"
                            >
                              <RotateCcw className={`w-3.5 h-3.5 ${isRegeneratingDoc === doc.doc_type ? 'animate-spin' : ''}`} />
                              <span>REGENERATE</span>
                            </button>
                          </div>
                        </div>

                        {/* Accordion Body */}
                        {isExpanded && (
                          <div className="p-6 border-t border-slate-850 bg-slate-950/20">
                            {isEditing ? (
                              <DocumentEditor
                                content={doc.content}
                                onSave={(newContent) => handleSaveDoc(doc.id, newContent)}
                                onApprove={() => handleApproveDoc(doc.id)}
                                onCancel={() => setEditingDocId(null)}
                              />
                            ) : (
                              <DocumentViewer content={doc.content} />
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              // Standard Documents View
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
                        <DocumentViewer content={selectedDoc.content} />
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
          </div>
        )}

        {activeTab === "build" && (
          <div className="space-y-6">
            {sprintGenerationProgress && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center min-h-[200px] text-center space-y-3">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
                <h4 className="text-base font-bold text-white uppercase font-mono">
                  {sprintGenerationProgress.status === "analyzing" ? "Analyzing Documentation" : "Generating Tasks"}
                </h4>
                <p className="text-sm text-slate-400">{sprintGenerationProgress.message}</p>
                <button
                  onClick={() => projectId && cancelSprintGeneration(projectId)}
                  className="px-4 py-1.5 rounded-full text-xs font-semibold bg-rose-500/10 border border-rose-500/25 text-rose-400 hover:bg-rose-500/20 active:bg-rose-500/30 transition-all cursor-pointer font-mono uppercase"
                >
                  Terminate
                </button>
              </div>
            )}

            {project.status === "doc_review" && !sprintGenerationProgress && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div className="space-y-1">
                  <h4 className="text-base font-bold text-white font-mono uppercase tracking-wider">Start Build Pipeline</h4>
                  <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
                    All blueprint documents have been generated. Click build below to approve all documents and launch the automated coding agent.
                  </p>
                </div>
                <button
                  onClick={handleApproveEverythingAndBuild}
                  className="w-full md:w-auto px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg text-sm transition-all border border-indigo-500/20 shadow shadow-indigo-600/20 font-mono uppercase whitespace-nowrap"
                >
                  BUILD APP
                </button>
              </div>
            )}

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

        {activeTab === "code" && (
          <div className="space-y-6">
            <FileBrowser projectId={projectId!} />
          </div>
        )}

        {activeTab === "setup" && (
          <div className="max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-base font-bold text-slate-200 font-mono mb-4">Post-Build Setup Guide</h3>
            <SetupChecklist steps={setupSteps} envTemplate={envTemplate} />
          </div>
        )}

        {activeTab === "run" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <SetupGate
                  steps={runStore.setupSteps}
                  onReady={() => {}}
                  onSave={(stepId, val) => projectId && runStore.saveEnvValue(projectId, stepId, val)}
                  onMark={(stepId, completed) => projectId && runStore.markStep(projectId, stepId, completed)}
                />
              </div>
              <div>
                <RunPanel
                  ready={runStore.ready}
                  installed={runStore.installStatus === "installed"}
                  status={runStore.runStatus}
                  backendUrl={runStore.backendUrl}
                  frontendUrl={runStore.frontendUrl}
                  onInstall={() => projectId && runStore.install(projectId)}
                  onStart={() => projectId && runStore.start(projectId)}
                  onStop={() => projectId && runStore.stop(projectId)}
                />
              </div>
            </div>
            {projectId && (
              <RunLogs
                projectId={projectId}
                backendLogs={runStore.backendLogs}
                frontendLogs={runStore.frontendLogs}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
