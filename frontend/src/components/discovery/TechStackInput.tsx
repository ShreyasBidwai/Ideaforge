import React, { useState, useEffect, useRef } from "react";
import { X, Search } from "lucide-react";
import apiClient from "../../services/api";
import Input from "../ui/Input";

interface TechStackInputProps {
  value: string[];
  onChange: (value: string[]) => void;
}

interface TechStackItem {
  name: string;
  category: string;
  subcategory: string;
}

export const TechStackInput: React.FC<TechStackInputProps> = ({ value, onChange }) => {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<TechStackItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
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
          (item) => !value.includes(item.name)
        );
        setSuggestions(filtered);
      } catch (err) {
        console.error("Error searching tech stack:", err);
      }
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [query, value]);

  const handleSelect = (techName: string) => {
    if (!value.includes(techName)) {
      onChange([...value, techName]);
    }
    setQuery("");
    setIsOpen(false);
  };

  const handleRemove = (techName: string) => {
    onChange(value.filter((item) => item !== techName));
  };

  return (
    <div ref={containerRef} className="relative w-full space-y-2">
      <Input
        label="Preferred Tech Stack (Optional)"
        placeholder="Type to search tech stack..."
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        icon={Search}
        id="tech-stack-search"
      />

      {isOpen && suggestions.length > 0 && (
        <ul className="absolute z-20 w-full mt-1 bg-slate-900 border border-white/10 rounded-xl max-h-60 overflow-y-auto shadow-2xl p-1.5 space-y-0.5">
          {suggestions.map((item) => (
            <li key={item.name}>
              <button
                type="button"
                onClick={() => handleSelect(item.name)}
                className="w-full text-left px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800 hover:text-white flex justify-between items-center"
              >
                <span>{item.name}</span>
                <span className="text-[10px] text-slate-500 uppercase tracking-wider bg-slate-950 px-2 py-0.5 rounded border border-white/5">
                  {item.subcategory}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {value.map((tech) => (
            <span
              key={tech}
              className="inline-flex items-center gap-1 bg-blue-600/20 text-blue-400 text-xs px-2.5 py-1 rounded-full border border-blue-500/20 font-medium"
            >
              {tech}
              <button
                type="button"
                onClick={() => handleRemove(tech)}
                className="hover:text-blue-200 focus:outline-none"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default TechStackInput;
