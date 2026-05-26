import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { MapPin, Sparkles } from "lucide-react";
import { useDiscoveryStore } from "../stores/discoveryStore";
import IndustryInput from "../components/discovery/IndustryInput";
import MaturitySelector from "../components/discovery/MaturitySelector";
import TechStackInput from "../components/discovery/TechStackInput";
import PainPointCard from "../components/discovery/PainPointCard";
import PainPointSkeleton from "../components/discovery/PainPointSkeleton";
import StreamProgress from "../components/discovery/StreamProgress";
import Input from "../components/ui/Input";

export const Discovery: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentSession,
    painPoints,
    isDiscovering,
    currentStep,
    error,
    createAndDiscover,
    clearSession,
  } = useDiscoveryStore();

  const [industry, setIndustry] = useState("");
  const [location, setLocation] = useState("");
  const [maturityLevel, setMaturityLevel] = useState("mvp");
  const [techStack, setTechStack] = useState<string[]>([]);
  const [errors, setErrors] = useState<{ industry?: string; location?: string }>({});

  const handleStartDiscovery = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: { industry?: string; location?: string } = {};
    if (!industry.trim()) {
      newErrors.industry = "Industry is required";
    }
    if (!location.trim()) {
      newErrors.location = "Location is required";
    }
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    setErrors({});

    try {
      await createAndDiscover(industry, location, maturityLevel, techStack);
    } catch (err) {
      console.error("Discovery error:", err);
    }
  };

  const showResults = currentSession !== null || isDiscovering;

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-8">
      {!showResults ? (
        // Phase 1: Input Form
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="max-w-2xl mx-auto bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-3xl p-8 shadow-2xl relative overflow-hidden"
        >
          {/* Decorative gradients */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl -z-10" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-violet-600/10 rounded-full blur-3xl -z-10" />

          <div className="text-center mb-8">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mb-2">
              Discover Industry Pain Points
            </h1>
            <p className="text-slate-400 text-sm sm:text-base">
              Enter an industry and location to uncover real problems worth solving
            </p>
          </div>

          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleStartDiscovery} className="space-y-6">
            <IndustryInput
              value={industry}
              onChange={setIndustry}
              error={errors.industry}
            />

            <Input
              label="Location"
              placeholder="Enter location, e.g. Mumbai, India or United States"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              error={errors.location}
              icon={MapPin}
              id="location"
            />

            <MaturitySelector
              value={maturityLevel}
              onChange={setMaturityLevel}
            />

            <TechStackInput
              value={techStack}
              onChange={setTechStack}
            />

            <button
              type="submit"
              disabled={isDiscovering}
              className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 transition-all flex items-center justify-center gap-2 mt-4 hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none"
            >
              <Sparkles size={18} />
              <span>Start Discovery</span>
            </button>
          </form>
        </motion.div>
      ) : (
        // Phase 2: Results / Loading Skeletons
        <div className="space-y-8">
          <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 shadow-xl">
            <div className="space-y-2">
              <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Active Discovery Workspace</div>
              <div className="flex flex-wrap gap-2 items-center">
                {currentSession && (
                  <>
                    <span className="bg-blue-600/15 text-blue-400 border border-blue-500/20 text-xs px-3.5 py-1.5 rounded-full font-semibold uppercase tracking-wider">
                      {currentSession.industry}
                    </span>
                    <span className="bg-slate-800 text-slate-300 border border-white/5 text-xs px-3.5 py-1.5 rounded-full font-semibold uppercase tracking-wider">
                      {currentSession.location}
                    </span>
                    <span className="bg-slate-800 text-slate-300 border border-white/5 text-xs px-3.5 py-1.5 rounded-full font-semibold uppercase tracking-wider">
                      {currentSession.maturity_level}
                    </span>
                  </>
                )}
                {!currentSession && isDiscovering && (
                  <>
                    <span className="bg-blue-600/15 text-blue-400 border border-blue-500/20 text-xs px-3.5 py-1.5 rounded-full font-semibold uppercase tracking-wider animate-pulse">
                      {industry || "Loading..."}
                    </span>
                    <span className="bg-slate-800 text-slate-300 border border-white/5 text-xs px-3.5 py-1.5 rounded-full font-semibold uppercase tracking-wider animate-pulse">
                      {location || "Loading..."}
                    </span>
                  </>
                )}
              </div>
            </div>
            <button
              onClick={clearSession}
              disabled={isDiscovering}
              className="text-slate-400 hover:text-white text-sm font-semibold transition-colors disabled:opacity-50"
            >
              Reset Session
            </button>
          </div>

          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm">
              {error}
            </div>
          )}

          {isDiscovering ? (
            <div className="space-y-8 animate-in fade-in duration-300">
              <StreamProgress currentStep={currentStep} />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <PainPointSkeleton />
                <PainPointSkeleton />
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {painPoints.map((pp, idx) => (
                <PainPointCard key={idx} painPoint={pp} index={idx} />
              ))}
            </div>
          )}

          {!isDiscovering && painPoints.length > 0 && (
            <div className="flex justify-end pt-4">
              <button
                onClick={() => navigate("/library")}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 transition-all hover:-translate-y-0.5 active:translate-y-0 flex items-center gap-2"
              >
                <span>Generate Problem Statements</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Discovery;
