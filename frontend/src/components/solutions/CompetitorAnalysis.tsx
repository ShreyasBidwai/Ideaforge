import React, { useEffect } from "react";
import { Search, Loader2, AlertCircle, ExternalLink, RefreshCw } from "lucide-react";
import { useCompetitorStore } from "../../stores/competitorStore";

interface CompetitorAnalysisProps {
  solutionId: string;
}

export const CompetitorAnalysis: React.FC<CompetitorAnalysisProps> = ({ solutionId }) => {
  const { analyses, fetchAnalysis, runAnalysis, refreshAnalysis } = useCompetitorStore();
  const analysis = analyses[solutionId];

  useEffect(() => {
    fetchAnalysis(solutionId);
  }, [solutionId, fetchAnalysis]);

  // Polling logic when researching
  useEffect(() => {
    if (analysis?.status === "researching") {
      const interval = setInterval(() => {
        fetchAnalysis(solutionId);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [analysis?.status, solutionId, fetchAnalysis]);

  const handleRun = async () => {
    await runAnalysis(solutionId);
  };

  const handleRefresh = async () => {
    await refreshAnalysis(solutionId);
  };

  if (!analysis) {
    return (
      <div className="mt-4 bg-slate-900/40 border border-white/5 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Search className="w-5 h-5 text-slate-400" />
          <div>
            <h4 className="text-sm font-medium text-white">Competitor Analysis</h4>
            <p className="text-xs text-slate-400">Research real-world competitors and market differentiation.</p>
          </div>
        </div>
        <button
          onClick={handleRun}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-colors"
        >
          Research Competitors
        </button>
      </div>
    );
  }

  if (analysis.status === "pending") {
    return (
      <div className="mt-4 bg-slate-900/40 border border-white/5 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Search className="w-5 h-5 text-slate-400" />
          <div>
            <h4 className="text-sm font-medium text-white">Competitor Analysis Pending</h4>
            <p className="text-xs text-slate-400">Ready to search and analyze market data.</p>
          </div>
        </div>
        <button
          onClick={handleRun}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-colors"
        >
          Start Research
        </button>
      </div>
    );
  }

  if (analysis.status === "researching") {
    return (
      <div className="mt-4 bg-slate-900/40 border border-white/5 rounded-xl p-6 flex flex-col items-center justify-center text-center gap-3">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" data-testid="researching-spinner" />
        <div>
          <h4 className="text-sm font-medium text-white">Researching Competitors...</h4>
          <p className="text-xs text-slate-400 max-w-md mt-1">
            Searching Tavily and synthesizing findings with Gemini. This may take up to a minute.
          </p>
        </div>
      </div>
    );
  }

  if (analysis.status === "failed") {
    return (
      <div className="mt-4 bg-red-950/20 border border-red-500/20 rounded-xl p-4 flex flex-col gap-3">
        <div className="flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <div className="flex-1">
            <h4 className="text-sm font-medium">Research Failed</h4>
            <p className="text-xs text-red-400/80">{analysis.error || "An unknown error occurred during research."}</p>
          </div>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-950/40 hover:bg-red-900/40 border border-red-500/30 text-white transition-colors"
          >
            <RefreshCw className="w-3 h-3" /> Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 border-t border-white/5 pt-6">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Competitor Analysis</h4>
        <button
          onClick={handleRefresh}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Research
        </button>
      </div>

      <div className="space-y-4">
        {/* Market Summary */}
        {analysis.market_summary && (
          <div className="bg-slate-900/30 border border-white/5 rounded-xl p-4">
            <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Market Summary</h5>
            <p className="text-slate-300 text-sm leading-relaxed">{analysis.market_summary}</p>
          </div>
        )}

        {/* Differentiation */}
        {analysis.differentiation && (
          <div className="bg-blue-950/10 border border-blue-500/10 rounded-xl p-4">
            <h5 className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2">Our Differentiation</h5>
            <p className="text-slate-300 text-sm leading-relaxed">{analysis.differentiation}</p>
          </div>
        )}

        {/* Competitors List */}
        {analysis.competitors && analysis.competitors.length > 0 ? (
          <div>
            <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Real-World Competitors</h5>
            <div className="grid gap-4 md:grid-cols-2">
              {analysis.competitors.map((comp, idx) => (
                <div key={idx} className="bg-slate-900/50 border border-white/5 rounded-xl p-4 flex flex-col justify-between" data-testid="competitor-item">
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h6 className="font-semibold text-white text-sm">{comp.name}</h6>
                      {comp.url && (
                        <a
                          href={comp.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-slate-500 hover:text-white transition-colors"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                    <p className="text-slate-400 text-xs leading-relaxed mb-3">{comp.description}</p>

                    {/* Metadata */}
                    <div className="flex flex-wrap gap-x-4 gap-y-2 mb-4 text-[11px] text-slate-500">
                      <div>
                        <span className="font-medium text-slate-400">Pricing:</span>{" "}
                        <span className="text-slate-300">{comp.pricing || "Unknown"}</span>
                      </div>
                      <div>
                        <span className="font-medium text-slate-400">Funding:</span>{" "}
                        <span className="text-slate-300">{comp.funding || "Unknown"}</span>
                      </div>
                    </div>

                    {/* Strengths & Weaknesses */}
                    <div className="space-y-2">
                      {comp.strengths && comp.strengths.length > 0 && (
                        <div>
                          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Strengths</div>
                          <ul className="list-disc pl-4 space-y-0.5 text-xs text-emerald-400/90">
                            {comp.strengths.map((str, sIdx) => (
                              <li key={sIdx}>{str}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {comp.weaknesses && comp.weaknesses.length > 0 && (
                        <div>
                          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Weaknesses</div>
                          <ul className="list-disc pl-4 space-y-0.5 text-xs text-red-400/90">
                            {comp.weaknesses.map((wk, wIdx) => (
                              <li key={wIdx}>{wk}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-slate-500 text-xs italic py-2">No real-world competitors found.</div>
        )}

        {/* Sources */}
        {analysis.sources && analysis.sources.length > 0 && (
          <div className="pt-2">
            <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Sources Consulted</h5>
            <div className="flex flex-wrap gap-2">
              {analysis.sources.map((src, idx) => (
                <a
                  key={idx}
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] bg-slate-900 text-slate-400 hover:text-white border border-white/5 transition-colors"
                >
                  {src.title || src.url} <ExternalLink className="w-2.5 h-2.5" />
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompetitorAnalysis;
