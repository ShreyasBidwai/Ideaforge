import React, { useState } from "react";
import hljs from "highlight.js";
import "highlight.js/styles/github-dark.css";
import { Copy, Check, Download } from "lucide-react";

interface CodeViewerProps {
  content: string;
  language?: string;
  filePath: string;
  onDownload?: () => void;
}

const getLanguageFromExtension = (path: string): string => {
  const ext = path.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "py":
      return "python";
    case "js":
    case "jsx":
      return "javascript";
    case "ts":
    case "tsx":
      return "typescript";
    case "json":
      return "json";
    case "md":
      return "markdown";
    case "html":
      return "xml";
    case "css":
      return "css";
    case "sh":
      return "bash";
    case "yml":
    case "yaml":
      return "yaml";
    default:
      return "plaintext";
  }
};

export const CodeViewer: React.FC<CodeViewerProps> = ({
  content,
  language,
  filePath,
  onDownload,
}) => {
  const [copied, setCopied] = useState(false);
  const lang = language || getLanguageFromExtension(filePath);

  const highlighted = (() => {
    try {
      return hljs.highlight(content, { language: lang }).value;
    } catch {
      return hljs.highlightAuto(content).value;
    }
  })();

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = content.split(/\r?\n/);
  // Ensure we show at least one line if content is empty
  if (lines.length === 1 && lines[0] === "") {
    lines.pop();
  }

  return (
    <div className="relative flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg select-text">
      {/* File Path Header */}
      <div className="flex items-center justify-between px-6 py-3 bg-slate-950 border-b border-slate-850">
        <span className="text-xs font-semibold text-slate-400 font-mono tracking-wide truncate">
          {filePath}
        </span>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-xs font-semibold border border-slate-800 rounded-md transition-colors text-slate-300 font-mono"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-mono">COPIED</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-400" />
                <span>COPY</span>
              </>
            )}
          </button>
          {onDownload && (
            <button
              onClick={onDownload}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-xs font-semibold border border-slate-800 rounded-md transition-colors text-slate-300 font-mono"
            >
              <Download className="w-3.5 h-3.5 text-slate-400" />
              <span>DOWNLOAD</span>
            </button>
          )}
        </div>
      </div>

      {/* Code Area */}
      <div className="flex-1 flex overflow-auto font-mono text-sm leading-6 bg-slate-900 p-4">
        {/* Line Numbers */}
        <div className="flex flex-col text-right text-slate-600 select-none pr-4 border-r border-slate-800/80 mr-4 font-mono min-w-[2.5rem]">
          {lines.map((_, idx) => (
            <span key={idx}>{idx + 1}</span>
          ))}
        </div>
        
        {/* Highlighted Code */}
        <pre className="flex-1 overflow-x-auto m-0 p-0 font-mono bg-transparent outline-none">
          <code
            className={`hljs language-${lang} font-mono`}
            dangerouslySetInnerHTML={{ __html: highlighted }}
          />
        </pre>
      </div>
    </div>
  );
};

export default CodeViewer;
