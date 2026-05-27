import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Pencil, X, Search, Check, Ban } from "lucide-react";
import apiClient from "../../services/api";

interface TechStackEditorProps {
  techStack: string[];
  onSave: (updated: string[]) => Promise<void> | any;
}

interface TechStackItem {
  name: string;
  category: string;
  subcategory: string;
}

const getCategoryColor = (techName: string) => {
  const cat = getCategoryByName(techName).toLowerCase();
  if (cat.includes("frontend") || cat.includes("styling")) return "bg-blue-500/10 text-blue-400 border border-blue-500/20";
  if (cat.includes("backend") || cat.includes("framework")) return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
  if (cat.includes("database") || cat.includes("db") || cat.includes("cache")) return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
  if (cat.includes("infra") || cat.includes("devops") || cat.includes("cloud")) return "bg-purple-500/10 text-purple-400 border border-purple-500/20";
  if (cat.includes("ai") || cat.includes("ml") || cat.includes("gemini") || cat.includes("openai")) return "bg-rose-500/10 text-rose-400 border border-rose-500/20";
  return "bg-slate-500/10 text-slate-400 border border-slate-500/20";
};

const getCategoryByName = (name: string): string => {
  const n = name.toLowerCase();
  if (["react", "next.js", "vue", "angular", "svelte", "tailwind", "css", "html", "js", "ts", "typescript", "javascript"].some(k => n.includes(k))) return "frontend";
  if (["fastapi", "django", "flask", "express", "node", "python", "go", "rust", "java", "spring"].some(k => n.includes(k))) return "backend";
  if (["postgres", "mysql", "mongo", "redis", "db", "sqlite", "sql", "cassandra", "dynamo"].some(k => n.includes(k))) return "database";
  if (["docker", "kubernetes", "aws", "gcp", "azure", "vercel", "netlify", "infra", "terraform"].some(k => n.includes(k))) return "infrastructure";
  if (["tensor", "pytorch", "openai", "gemini", "hugging", "ml", "ai", "langchain", "llama"].some(k => n.includes(k))) return "ai_ml";
  return "other";
};

const TechStackEditor: React.FC<TechStackEditorProps> = ({ techStack, onSave }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [tempStack, setTempStack] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<TechStackItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  useEffect(() => {
    if (query.trim() === "") {
      setSuggestions([]);
      return;
    }

    const delayDebounce = setTimeout(async () => {
      try {
        const response = await apiClient.get<TechStackItem[]>("/api/v1/tech-stacks/search", {
          params: { q: query },
        });
        const filtered = (response.data || []).filter(
          (item) => !tempStack.includes(item.name)
        );
        setSuggestions(filtered);
      } catch (err) {
        console.error("Error searching tech stack:", err);
      }
    }, 200);

    return () => clearTimeout(delayDebounce);
  }, [query, tempStack]);

  const handleStartEdit = () => {
    setTempStack([...techStack]);
    setQuery("");
    setIsEditing(true);
  };

  const handleCancel = () => {
    setTempStack([]);
    setQuery("");
    setIsEditing(false);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(tempStack);
      setIsEditing(false);
    } catch (err) {
      console.error("Failed to save tech stack", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAdd = (techName: string) => {
    if (!tempStack.includes(techName)) {
      setTempStack([...tempStack, techName]);
    }
    setQuery("");
    setIsOpen(false);
  };

  const handleRemove = (techName: string) => {
    setTempStack(tempStack.filter((item) => item !== techName));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Tech Stack
        </h5>
        {!isEditing && (
          <button
            onClick={handleStartEdit}
            data-testid="edit-tech-stack"
            aria-label="Edit"
            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {!isEditing ? (
        <div className="flex flex-wrap gap-1.5">
          {techStack.length > 0 ? (
            techStack.map((tech) => (
              <span
                key={tech}
                className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full font-medium ${getCategoryColor(
                  tech
                )}`}
              >
                {tech}
              </span>
            ))
          ) : (
            <span className="text-sm text-slate-500 italic">No technologies defined</span>
          )}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          transition={{ duration: 0.15 }}
          ref={containerRef}
          className="space-y-3 p-3 bg-slate-900/40 rounded-xl border border-white/5 overflow-hidden"
        >
          {/* Temp Stack Tags */}
          <div className="flex flex-wrap gap-1.5 min-h-[32px] p-1 bg-slate-950/20 rounded-lg border border-white/5">
            {tempStack.length > 0 ? (
              tempStack.map((tech) => (
                <span
                  key={tech}
                  className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium ${getCategoryColor(
                    tech
                  )}`}
                >
                  {tech}
                  <button
                    type="button"
                    onClick={() => handleRemove(tech)}
                    aria-label={`Remove ${tech}`}
                    className="hover:scale-110 focus:outline-none transition-transform"
                  >
                    <X className="w-3.5 h-3.5 text-slate-400 hover:text-slate-200" />
                  </button>
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500 italic p-1">No tech selected</span>
            )}
          </div>

          {/* Input & Autocomplete */}
          <div className="relative">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search and add technologies..."
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setIsOpen(true);
                }}
                onFocus={() => setIsOpen(true)}
                className="w-full bg-slate-950 border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>

            {isOpen && query.trim() !== "" && (
              <div className="absolute z-30 w-full mt-1 bg-slate-900 border border-white/10 rounded-lg max-h-48 overflow-y-auto shadow-2xl p-1">
                {suggestions.length === 0 ? (
                  <div className="px-3 py-1.5 text-xs text-slate-500">
                    No matching tech found
                  </div>
                ) : (
                  suggestions.map((item) => (
                    <button
                      key={item.name}
                      type="button"
                      onClick={() => handleAdd(item.name)}
                      className="w-full text-left px-3 py-1.5 rounded text-xs text-slate-300 hover:bg-slate-800 hover:text-white transition-colors flex justify-between items-center"
                    >
                      <span>{item.name}</span>
                      <span className="text-[9px] uppercase tracking-wider text-slate-500">
                        {item.subcategory}
                      </span>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={handleCancel}
              disabled={isSaving}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 rounded-lg transition-colors flex items-center gap-1"
            >
              <Ban className="w-3.5 h-3.5" />
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white rounded-lg transition-colors flex items-center gap-1"
            >
              <Check className="w-3.5 h-3.5" />
              Save
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default TechStackEditor;
