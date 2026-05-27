import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderCode, PlusCircle, ArrowRight, Calendar } from 'lucide-react';
import apiClient from '../services/api';

interface Project {
  id: string;
  name: string;
  description?: string;
  status: string;
  industry: string;
  tech_stack: string[];
  created_at: string;
}

export default function ProjectsList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    apiClient.get('/api/v1/projects')
      .then((res) => {
        setProjects(res.data || []);
        setLoading(false);
      })
      .catch((e) => {
        console.error(e);
        setLoading(false);
      });
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'doc_generation':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'doc_review':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'building':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'paused':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
      case 'rate_limited':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'completed':
      case 'complete':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'failed':
        return 'bg-red-500/10 text-red-400 border-red-500/20';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700/60';
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-400 font-mono">
        Loading projects...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6 lg:p-8 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white font-mono uppercase">Projects</h1>
          <p className="text-sm text-slate-400 mt-1">Manage and track your active application generation builds.</p>
        </div>
      </div>

      {projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-2xl py-16 px-4 text-center max-w-xl mx-auto mt-8">
          <FolderCode className="w-12 h-12 text-slate-700 mb-4" />
          <h3 className="text-lg font-semibold text-slate-300">No projects yet</h3>
          <p className="text-sm text-slate-500 mt-2 max-w-sm">
            No projects yet. Approve a solution to create your first project.
          </p>
          <button
            onClick={() => navigate('/approvals')}
            className="mt-6 inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition font-mono border border-blue-500/20"
          >
            <PlusCircle className="w-4 h-4" />
            <span>GO TO APPROVALS</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div
              key={proj.id}
              onClick={() => navigate(`/projects/${proj.id}`)}
              className="group relative bg-slate-900 border border-slate-800/80 hover:border-slate-700 hover:bg-slate-850/60 rounded-2xl p-6 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl"
            >
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-base font-bold text-white tracking-tight group-hover:text-blue-400 transition-colors">
                    {proj.name}
                  </h3>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider font-mono border ${getStatusColor(proj.status)}`}>
                    {proj.status}
                  </span>
                </div>

                {proj.description && (
                  <p className="text-sm text-slate-400 line-clamp-2 leading-relaxed">
                    {proj.description}
                  </p>
                )}

                <div className="flex flex-wrap gap-1.5 pt-2">
                  <span className="bg-slate-850 border border-slate-800 text-slate-400 text-[10px] font-bold px-2 py-0.5 rounded font-mono">
                    {proj.industry}
                  </span>
                  {Array.isArray(proj.tech_stack) && proj.tech_stack.slice(0, 3).map((tech, i) => (
                    <span key={i} className="bg-blue-500/5 border border-blue-500/10 text-blue-400 text-[10px] font-bold px-2 py-0.5 rounded font-mono">
                      {tech}
                    </span>
                  ))}
                  {Array.isArray(proj.tech_stack) && proj.tech_stack.length > 3 && (
                    <span className="bg-slate-850 border border-slate-800 text-slate-500 text-[10px] font-bold px-2 py-0.5 rounded font-mono">
                      +{proj.tech_stack.length - 3} more
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-slate-800/60 pt-4 mt-6">
                <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-mono">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>{new Date(proj.created_at).toLocaleDateString()}</span>
                </div>
                <div className="text-xs font-semibold text-blue-500 flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
                  <span>Open Blueprint</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
