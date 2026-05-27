import React, { useState } from "react";
import {
  File,
  Folder,
  FolderOpen,
  FileCode,
  FileText,
  FileJson,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

export interface FileNode {
  name: string;
  type: "directory" | "file";
  size?: number;
  children?: FileNode[];
}

interface FileTreeProps {
  tree: FileNode;
  onSelectFile: (path: string) => void;
  activeFilePath?: string;
  currentPath?: string;
  isRoot?: boolean;
}

const getFileIcon = (name: string) => {
  const ext = name.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "py":
    case "js":
    case "jsx":
    case "ts":
    case "tsx":
    case "html":
    case "css":
    case "sh":
      return <FileCode className="w-4 h-4 text-blue-400" />;
    case "json":
      return <FileJson className="w-4 h-4 text-amber-400" />;
    case "md":
      return <FileText className="w-4 h-4 text-emerald-400" />;
    default:
      return <File className="w-4 h-4 text-slate-400" />;
  }
};

export const FileTree: React.FC<FileTreeProps> = ({
  tree,
  onSelectFile,
  activeFilePath,
  currentPath = "",
  isRoot = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(isRoot);

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (tree.type === "file") {
      onSelectFile(currentPath);
    } else {
      setIsExpanded(!isExpanded);
    }
  };

  const isActive = activeFilePath === currentPath;

  if (tree.type === "file") {
    return (
      <div
        onClick={handleClick}
        className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg cursor-pointer transition-colors text-xs font-mono select-none ${
          isActive
            ? "bg-blue-500/10 text-blue-400 font-semibold border-l-2 border-blue-500 pl-2.5"
            : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
        }`}
      >
        {getFileIcon(tree.name)}
        <span className="truncate">{tree.name}</span>
      </div>
    );
  }

  // Directory node
  return (
    <div className="space-y-1">
      {/* Directory Row */}
      {!isRoot ? (
        <div
          onClick={handleClick}
          className="flex items-center justify-between px-3 py-1.5 rounded-lg cursor-pointer hover:bg-slate-900/40 text-slate-300 hover:text-white transition-colors text-xs font-mono select-none"
        >
          <div className="flex items-center space-x-2 truncate">
            {isExpanded ? (
              <FolderOpen className="w-4 h-4 text-amber-500/80" />
            ) : (
              <Folder className="w-4 h-4 text-amber-500/80" />
            )}
            <span className="truncate">{tree.name}</span>
          </div>
          <button
            onClick={handleToggle}
            className="text-slate-500 hover:text-slate-300 focus:outline-none"
          >
            {isExpanded ? (
              <ChevronDown className="w-3.5 h-3.5" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      ) : (
        // Root Directory display
        <div
          onClick={handleClick}
          className="flex items-center space-x-2 px-2 py-1.5 text-xs font-bold font-mono text-slate-300 border-b border-slate-800/80 pb-2 mb-2 select-none cursor-pointer"
        >
          {isExpanded ? (
            <FolderOpen className="w-4 h-4 text-blue-500" />
          ) : (
            <Folder className="w-4 h-4 text-blue-500" />
          )}
          <span>{tree.name}</span>
        </div>
      )}

      {/* Children */}
      {isExpanded && tree.children && (
        <div className={!isRoot ? "pl-4 space-y-1 border-l border-slate-800/60 ml-3.5" : "space-y-1"}>
          {tree.children.map((child, index) => {
            const childPath = currentPath
              ? `${currentPath}/${child.name}`
              : child.name;
            return (
              <FileTree
                key={index}
                tree={child}
                onSelectFile={onSelectFile}
                activeFilePath={activeFilePath}
                currentPath={childPath}
                isRoot={false}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FileTree;
