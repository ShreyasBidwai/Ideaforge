import React, { useState, useEffect, useRef } from "react";
import { X, Search } from "lucide-react";
import apiClient from "../../services/api";
import Input from "../ui/Input";

interface TechStackInputProps {
  value?: string[];
  selected?: string[];
  onChange: (value: string[]) => void;
}

interface TechStackItem {
  name: string;
  category: string;
  subcategory: string;
}

const getCategoryColor = (techName: string, categoryFromApi?: string) => {
  const cat = (categoryFromApi || getCategoryByName(techName)).toLowerCase();
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

export const TechStackInput: React.FC<TechStackInputProps> = ({ value, selected, onChange }) => {
  const activeSelected = selected || value || [];
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<TechStackItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
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
          (item) => !activeSelected.includes(item.name)
        );
        setSuggestions(filtered);
        setFocusedIndex(filtered.length > 0 ? 0 : -1);
      } catch (err) {
        console.error("Error searching tech stack:", err);
      }
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [query, activeSelected]);

  const handleSelect = (techName: string) => {
    if (activeSelected.length >= 10) return;
    if (!activeSelected.includes(techName)) {
      onChange([...activeSelected, techName]);
    }
    setQuery("");
    setIsOpen(false);
    setFocusedIndex(-1);
  };

  const handleRemove = (techName: string) => {
    onChange(activeSelected.filter((item) => item !== techName));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIndex((prev) => (suggestions.length > 0 ? (prev + 1) % suggestions.length : -1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIndex((prev) => (suggestions.length > 0 ? (prev - 1 + suggestions.length) % suggestions.length : -1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (focusedIndex >= 0 && focusedIndex < suggestions.length) {
        handleSelect(suggestions[focusedIndex].name);
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  // Group suggestions by category
  const grouped: { [category: string]: TechStackItem[] } = {};
  suggestions.forEach((item) => {
    const cat = item.category || "Other";
    if (!grouped[cat]) {
      grouped[cat] = [];
    }
    grouped[cat].push(item);
  });

  // Calculate global indices for grouped rendering keyboard support
  let globalItemIndex = 0;

  return (
    <div ref={containerRef} className="relative w-full space-y-2" onKeyDown={handleKeyDown}>
      <Input
        label="Preferred Tech Stack (Optional)"
        placeholder="Search technologies..."
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        icon={Search}
        id="tech-stack-search"
        disabled={activeSelected.length >= 10}
      />

      {activeSelected.length >= 10 && (
        <p className="text-amber-500 text-xs mt-1">
          Maximum limit of 10 tech stacks reached.
        </p>
      )}

      {isOpen && query.trim() !== "" && (
        <div className="absolute z-20 w-full mt-1 bg-slate-900 border border-white/10 rounded-xl max-h-60 overflow-y-auto shadow-2xl p-1.5">
          {suggestions.length === 0 ? (
            <div className="px-3 py-2 text-sm text-slate-500">
              No technologies found matching '{query}'
            </div>
          ) : (
            Object.entries(grouped).map(([category, items]) => (
              <div key={category} className="space-y-1">
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider px-3 py-1 bg-slate-950/40 rounded">
                  {category}
                </div>
                {items.map((item) => {
                  const currentGlobalIndex = globalItemIndex++;
                  const isFocused = currentGlobalIndex === focusedIndex;

                  return (
                    <button
                      key={item.name}
                      type="button"
                      onClick={() => handleSelect(item.name)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex justify-between items-center ${
                        isFocused
                          ? "bg-blue-600 text-white font-medium"
                          : "text-slate-300 hover:bg-slate-800 hover:text-white"
                      }`}
                    >
                      <span>{item.name}</span>
                      <span
                        className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border ${
                          isFocused
                            ? "bg-blue-700 border-blue-500 text-blue-200"
                            : "bg-slate-950 border-white/5 text-slate-500"
                        }`}
                      >
                        {item.subcategory}
                      </span>
                    </button>
                  );
                })}
              </div>
            ))
          )}
        </div>
      )}

      {activeSelected.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {activeSelected.map((tech) => (
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
                className="hover:scale-110 focus:outline-none transition-transform font-bold"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default TechStackInput;
