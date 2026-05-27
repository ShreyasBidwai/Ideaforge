import React, { useState } from 'react';
import DocumentViewer from './DocumentViewer';

interface DocumentEditorProps {
  content: string;
  onSave: (newContent: string) => void | Promise<void>;
  onApprove: () => void | Promise<void>;
  onCancel: () => void | Promise<void>;
}

const DocumentEditor: React.FC<DocumentEditorProps> = ({
  content,
  onSave,
  onApprove,
  onCancel,
}) => {
  const [val, setVal] = useState(content);
  const [mode, setMode] = useState<'edit' | 'preview' | 'split'>('split');

  const insertMarkdown = (syntax: string) => {
    setVal((prev) => prev + syntax);
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 bg-zinc-900 border-b border-zinc-800 flex-wrap gap-2">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => insertMarkdown('**bold**')}
            className="px-2.5 py-1 text-sm font-semibold rounded bg-zinc-800 text-zinc-200 hover:bg-zinc-700 transition"
          >
            B
          </button>
          <button
            onClick={() => insertMarkdown('*italic*')}
            className="px-2.5 py-1 text-sm font-semibold italic rounded bg-zinc-800 text-zinc-200 hover:bg-zinc-700 transition"
          >
            I
          </button>
          <button
            onClick={() => insertMarkdown('\n# Heading 1\n')}
            className="px-2.5 py-1 text-sm font-semibold rounded bg-zinc-800 text-zinc-200 hover:bg-zinc-700 transition"
          >
            H1
          </button>
          <button
            onClick={() => insertMarkdown('\n- List item\n')}
            className="px-2.5 py-1 text-sm font-semibold rounded bg-zinc-800 text-zinc-200 hover:bg-zinc-700 transition"
          >
            List
          </button>
          <button
            onClick={() => insertMarkdown('\n```python\n\n```\n')}
            className="px-2.5 py-1 text-sm font-semibold rounded bg-zinc-800 text-zinc-200 hover:bg-zinc-700 transition"
          >
            Code
          </button>
        </div>

        <div className="flex items-center space-x-1 bg-zinc-950 p-1 rounded-lg border border-zinc-800">
          <button
            onClick={() => setMode('edit')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition ${
              mode === 'edit' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Edit
          </button>
          <button
            onClick={() => setMode('preview')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition ${
              mode === 'preview' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Preview
          </button>
          <button
            onClick={() => setMode('split')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition ${
              mode === 'split' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Split
          </button>
        </div>
      </div>

      {/* Editor Content Area */}
      <div className="flex flex-1 min-h-[400px] divide-x divide-zinc-800">
        {(mode === 'edit' || mode === 'split') && (
          <textarea
            value={val}
            onChange={(e) => setVal(e.target.value)}
            className="flex-1 p-4 bg-zinc-950 text-zinc-200 font-mono text-sm focus:outline-none resize-none min-h-[400px]"
            placeholder="Write markdown here..."
          />
        )}
        {(mode === 'preview' || mode === 'split') && (
          <div className="flex-1 p-4 bg-zinc-950 overflow-y-auto max-h-[600px] min-h-[400px]">
            <DocumentViewer content={val} />
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between px-6 py-4 bg-zinc-900 border-t border-zinc-800">
        <button
          onClick={() => onCancel()}
          className="px-4 py-2 text-sm font-medium rounded bg-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 transition"
        >
          Cancel
        </button>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => onSave(val)}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-lg shadow-indigo-600/20 transition"
          >
            Save
          </button>
          <button
            onClick={() => onApprove()}
            className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg shadow-lg shadow-emerald-600/20 transition"
          >
            Approve
          </button>
        </div>
      </div>
    </div>
  );
};

export default DocumentEditor;
