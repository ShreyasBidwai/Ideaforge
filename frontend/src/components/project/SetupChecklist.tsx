import React, { useState } from 'react';
import { CheckSquare, Square, Clipboard, Check, FileCode, Download } from 'lucide-react';

interface Step {
  label: string;
  command: string;
}

interface SetupChecklistProps {
  steps: Step[];
  envTemplate?: string;
}

export default function SetupChecklist({ steps, envTemplate }: SetupChecklistProps) {
  const [checkedSteps, setCheckedSteps] = useState<Record<number, boolean>>({});
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [copiedEnv, setCopiedEnv] = useState(false);

  const toggleStep = (index: number) => {
    setCheckedSteps((prev) => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const copyEnv = () => {
    if (!envTemplate) return;
    navigator.clipboard.writeText(envTemplate);
    setCopiedEnv(true);
    setTimeout(() => setCopiedEnv(false), 2000);
  };

  const downloadEnv = () => {
    if (!envTemplate) return;
    const blob = new Blob([envTemplate], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = '.env.example';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Checklist items */}
      <div className="space-y-4">
        <h3 className="text-base font-semibold text-slate-200 font-mono">Setup Steps</h3>
        <div className="space-y-3">
          {steps.map((step, idx) => {
            const isChecked = !!checkedSteps[idx];
            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border transition-all flex items-start space-x-3 ${
                  isChecked
                    ? 'bg-emerald-500/5 border-emerald-500/20 text-slate-400'
                    : 'bg-slate-800/30 border-slate-700/50 text-slate-200'
                }`}
              >
                <button
                  onClick={() => toggleStep(idx)}
                  className="mt-0.5 text-slate-400 hover:text-slate-200 transition-colors flex-shrink-0"
                >
                  {isChecked ? (
                    <CheckSquare className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <Square className="w-5 h-5" />
                  )}
                </button>

                <div className="flex-1 space-y-2">
                  <p className={`text-sm font-medium ${isChecked ? 'line-through text-slate-500' : ''}`}>
                    {step.label}
                  </p>
                  
                  {step.command && (
                    <div className="relative bg-slate-900 border border-slate-800 rounded-lg p-3 font-mono text-xs flex items-center justify-between text-slate-300">
                      <span className="break-all">{step.command}</span>
                      <button
                        onClick={() => copyToClipboard(step.command, idx)}
                        className="ml-4 p-1 hover:bg-slate-800 rounded text-slate-500 hover:text-slate-300 transition-colors flex-shrink-0"
                        title="Copy command"
                      >
                        {copiedIndex === idx ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Clipboard className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Env config file template */}
      {envTemplate && (
        <div className="space-y-3 border-t border-slate-800 pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FileCode className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-slate-200 font-mono">Environment File Template (.env)</h3>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={copyEnv}
                className="flex items-center space-x-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700/60 text-xs font-semibold font-mono transition-colors"
              >
                {copiedEnv ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span>COPIED</span>
                  </>
                ) : (
                  <>
                    <Clipboard className="w-3.5 h-3.5" />
                    <span>COPY</span>
                  </>
                )}
              </button>
              <button
                onClick={downloadEnv}
                className="flex items-center space-x-1 px-2.5 py-1 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 rounded border border-blue-500/20 text-xs font-semibold font-mono transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>DOWNLOAD</span>
              </button>
            </div>
          </div>

          <pre className="bg-slate-900 border border-slate-800 rounded-xl p-4 font-mono text-xs text-slate-400 overflow-x-auto leading-relaxed">
            {envTemplate}
          </pre>
        </div>
      )}
    </div>
  );
}
