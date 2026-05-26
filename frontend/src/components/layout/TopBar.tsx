import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LogOut, Menu } from "lucide-react";
import { useAuthStore } from "../../stores/authStore";
import { Breadcrumbs } from "./Breadcrumbs";

interface TopBarProps {
  onMenuClick: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onMenuClick }) => {
  const { user, logout } = useAuthStore();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const getInitials = (name: string) => {
    if (!name) return "";
    const parts = name.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return parts[0] ? parts[0][0].toUpperCase() : "";
  };

  const initials = user?.full_name ? getInitials(user.full_name) : "U";

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-white/5 bg-slate-950/80 px-6 backdrop-blur-md">
      {/* Left side */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onMenuClick}
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-900 hover:text-white md:hidden"
          aria-label="Toggle menu"
        >
          <Menu size={20} />
        </button>
        <Breadcrumbs />
      </div>

      {/* Right side */}
      <div className="relative">
        <button
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 font-bold text-white shadow-lg shadow-blue-600/20 transition-all hover:bg-blue-700 hover:scale-105"
        >
          {initials}
        </button>

        <AnimatePresence>
          {dropdownOpen && (
            <>
              {/* Invisible backdrop to close the dropdown */}
              <div
                className="fixed inset-0 z-40"
                onClick={() => setDropdownOpen(false)}
              />
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 mt-2 w-56 origin-top-right rounded-xl border border-white/5 bg-slate-900 p-2 text-white shadow-2xl z-50 backdrop-blur-sm"
              >
                {user && (
                  <div className="border-b border-white/5 px-4 py-3">
                    <p className="text-sm font-semibold truncate">
                      {user.full_name}
                    </p>
                    <p className="text-xs text-slate-400 truncate mt-0.5">
                      {user.email}
                    </p>
                  </div>
                )}
                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    logout();
                  }}
                  className="flex w-full items-center space-x-2 rounded-lg px-4 py-2 text-sm text-rose-400 hover:bg-rose-500/10 transition-colors mt-1"
                >
                  <LogOut size={16} />
                  <span>Log out</span>
                </button>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
};
