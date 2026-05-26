import React, { useState, useEffect, useRef } from "react";
import Input from "../ui/Input";
import { Briefcase } from "lucide-react";

interface IndustryInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

const commonIndustries = [
  "Healthcare",
  "Fintech",
  "EdTech",
  "Logistics",
  "Agriculture",
  "Real Estate",
  "E-commerce",
  "Manufacturing",
  "Legal Tech",
  "InsurTech",
  "HR Tech",
  "PropTech",
  "FoodTech",
  "CleanTech",
];

export const IndustryInput: React.FC<IndustryInputProps> = ({ value, onChange, error }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [filtered, setFiltered] = useState<string[]>([]);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (value.trim() === "") {
      setFiltered(commonIndustries);
    } else {
      const query = value.toLowerCase();
      setFiltered(
        commonIndustries.filter((item) => item.toLowerCase().includes(query))
      );
    }
    setActiveIndex(-1);
  }, [value]);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) {
      if (e.key === "ArrowDown") {
        setIsOpen(true);
      }
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1) % filtered.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((prev) => (prev - 1 + filtered.length) % filtered.length);
    } else if (e.key === "Enter") {
      if (activeIndex >= 0 && activeIndex < filtered.length) {
        e.preventDefault();
        onChange(filtered[activeIndex]);
        setIsOpen(false);
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const handleSelect = (item: string) => {
    onChange(item);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative w-full">
      <Input
        label="Industry"
        placeholder="Enter or select industry"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={handleKeyDown}
        icon={Briefcase}
        error={error}
        id="industry"
      />
      {isOpen && filtered.length > 0 && (
        <ul className="absolute z-30 w-full mt-1 bg-slate-900 border border-white/10 rounded-xl max-h-60 overflow-y-auto shadow-2xl p-1.5 space-y-0.5">
          {filtered.map((item, index) => (
            <li key={item}>
              <button
                type="button"
                onClick={() => handleSelect(item)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  index === activeIndex
                    ? "bg-blue-600 text-white font-medium"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                {item}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default IndustryInput;
