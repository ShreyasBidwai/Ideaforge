import React, { useEffect, useState, useMemo } from "react";
import { Folder, Loader2 } from "lucide-react";
import apiClient from "../../services/api";
import FileTree, { FileNode } from "./FileTree";
import CodeViewer from "./CodeViewer";

interface FileBrowserProps {
  projectId: string;
}

const getFileStats = (node: FileNode): { count: number; totalSize: number } => {
  if (node.type === "file") {
    return { count: 1, totalSize: node.size || 0 };
  }
  let count = 0;
  let totalSize = 0;
  if (node.children) {
    node.children.forEach((child) => {
      const stats = getFileStats(child);
      count += stats.count;
      totalSize += stats.totalSize;
    });
  }
  return { count, totalSize };
};

const formatSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

export const FileBrowser: React.FC<FileBrowserProps> = ({ projectId }) => {
  const [tree, setTree] = useState<FileNode | null>(null);
  const [activeFilePath, setActiveFilePath] = useState<string>("");
  const [activeFileContent, setActiveFileContent] = useState<string>("");
  const [isLoadingTree, setIsLoadingTree] = useState<boolean>(true);
  const [isLoadingContent, setIsLoadingContent] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTree = async () => {
      setIsLoadingTree(true);
      setError(null);
      try {
        const res = await apiClient.get(`/api/v1/projects/${projectId}/files`);
        setTree(res.data);
      } catch (err) {
        console.error("Failed to load project structure:", err);
        setError("Failed to load project files");
      } finally {
        setIsLoadingTree(false);
      }
    };

    fetchTree();
  }, [projectId]);

  const stats = useMemo(() => {
    if (!tree) return { count: 0, totalSize: 0 };
    return getFileStats(tree);
  }, [tree]);

  const handleSelectFile = async (path: string) => {
    setActiveFilePath(path);
    setIsLoadingContent(true);
    try {
      const res = await apiClient.get(`/api/v1/projects/${projectId}/files/${path}`);
      setActiveFileContent(res.data.content);
    } catch (err) {
      console.error(`Failed to load content for ${path}:`, err);
      setActiveFileContent("Error: Failed to load file content.");
    } finally {
      setIsLoadingContent(false);
    }
  };

  const handleDownload = () => {
    if (!activeFileContent || !activeFilePath) return;
    const element = document.createElement("a");
    const file = new Blob([activeFileContent], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = activeFilePath.split("/").pop() || "file";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="flex flex-col h-[650px] bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Workspace Area */}
      <div className="flex-1 flex min-h-0">
        {/* Left Panel: Directory Tree */}
        <div className="w-[30%] border-r border-slate-800 bg-slate-900/30 flex flex-col min-h-0">
          <div className="px-4 py-3 bg-slate-900/50 border-b border-slate-850 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 font-mono tracking-wider">PROJECT WORKSPACE</span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {isLoadingTree ? (
              <div className="flex flex-col items-center justify-center h-full space-y-2 text-slate-500 font-mono text-xs">
                <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                <span>Scanning structure...</span>
              </div>
            ) : error ? (
              <div className="text-red-400 text-xs font-mono p-4 text-center">
                {error}
              </div>
            ) : tree ? (
              <FileTree
                tree={tree}
                onSelectFile={handleSelectFile}
                activeFilePath={activeFilePath}
              />
            ) : (
              <div className="text-slate-500 text-xs font-mono p-4 text-center">
                Empty project
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Content Viewer */}
        <div className="w-[70%] bg-slate-900/10 flex flex-col min-h-0">
          {isLoadingContent ? (
            <div className="flex-1 flex flex-col items-center justify-center space-y-3 bg-slate-900/40 text-slate-400 font-mono text-sm">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <span>Fetching file content...</span>
            </div>
          ) : activeFilePath ? (
            <div className="flex-1 min-h-0 p-4">
              <CodeViewer
                content={activeFileContent}
                filePath={activeFilePath}
                onDownload={handleDownload}
              />
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 font-mono text-sm bg-slate-900/20">
              <Folder className="w-12 h-12 text-slate-700 mb-3" />
              <span>Select a file from the workspace to begin code review.</span>
            </div>
          )}
        </div>
      </div>

      {/* Footer Area */}
      <div className="px-6 py-2.5 bg-slate-950 border-t border-slate-850 flex items-center justify-between text-[11px] font-mono text-slate-500">
        <div className="flex items-center space-x-4">
          <span>Files: <strong className="text-slate-400">{stats.count}</strong></span>
          <span>Size: <strong className="text-slate-400">{formatSize(stats.totalSize)}</strong></span>
        </div>
        <div>
          <span>Powered by Claude Code Engine</span>
        </div>
      </div>
    </div>
  );
};

export default FileBrowser;
