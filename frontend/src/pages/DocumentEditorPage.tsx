import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../services/api';
import DocumentEditor from '../components/project/DocumentEditor';

export default function DocumentEditorPage() {
  const { projectId, docId } = useParams<{ projectId: string; docId: string }>();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId || !docId) return;
    apiClient.get(`/api/v1/projects/${projectId}/documents/${docId}`)
      .then((res) => {
        setDoc(res.data);
        setLoading(false);
      })
      .catch((e) => {
        console.error(e);
        setLoading(false);
      });
  }, [projectId, docId]);

  const handleSave = async (newContent: string) => {
    if (!projectId || !docId) return;
    try {
      await apiClient.patch(`/api/v1/projects/${projectId}/documents/${docId}`, { content: newContent });
      navigate(`/projects/${projectId}`);
    } catch (e) {
      console.error(e);
    }
  };

  const handleApprove = async () => {
    if (!projectId || !docId) return;
    try {
      await apiClient.post(`/api/v1/projects/${projectId}/documents/${docId}/approve`);
      navigate(`/projects/${projectId}`);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-400 font-mono">
        Loading document editor...
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-400 font-mono">
        Document not found
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6 lg:p-8 space-y-6">
      <h1 className="text-xl font-bold text-white font-mono uppercase">Edit {doc.title}</h1>
      <DocumentEditor
        content={doc.content}
        onSave={handleSave}
        onApprove={handleApprove}
        onCancel={() => navigate(`/projects/${projectId}`)}
      />
    </div>
  );
}
