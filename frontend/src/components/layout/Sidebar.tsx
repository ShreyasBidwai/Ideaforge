import React from "react";
import { Link, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  Library,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  setCollapsed,
  mobileOpen,
  setMobileOpen,
}) => {
  const navItems = [
    { name: "Dashboard", path: "/", icon: LayoutDashboard },
    { name: "Discovery", path: "/discovery", icon: Search },
    { name: "Problem Library", path: "/library", icon: Library },
    { name: "Approvals", path: "/approvals", icon: CheckCircle },
  ];

  const handleToggle = () => {
    const nextState = !collapsed;
    setCollapsed(nextState);
    localStorage.setItem("sidebar_collapsed", String(nextState));
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed bottom-0 top-0 left-0 z-50 flex flex-col border-r border-white/5 bg-slate-900 transition-all duration-200 ease-in-out md:static
          ${mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
          ${collapsed ? "w-[72px]" : "w-[260px]"}
        `}
      >
        {/* Top Header/Logo */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-white/5">
          <Link to="/" className="flex items-center space-x-2 overflow-hidden">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 font-bold text-white shadow-lg shadow-blue-600/30">
              IF
            </span>
            {!collapsed && (
              <span className="text-xl font-medium tracking-tight text-white">
                idea<span className="font-extrabold text-blue-500">forge</span>
              </span>
            )}
          </Link>
          <button
            onClick={() => setMobileOpen(false)}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white md:hidden"
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1 py-4 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `
                  flex items-center space-x-3 py-3 border-l-[3px] transition-all duration-150 font-medium
                  ${collapsed ? "px-5" : "px-4"}
                  ${
                    isActive
                      ? "bg-blue-600/10 border-blue-500 text-white"
                      : "border-transparent text-slate-400 hover:bg-slate-800/40 hover:text-white"
                  }
                `}
                onClick={() => setMobileOpen(false)}
              >
                <Icon size={20} className="flex-shrink-0" />
                {!collapsed && (
                  <span className="text-sm truncate">{item.name}</span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Bottom Toggle Button */}
        <div className="border-t border-white/5 p-4 flex justify-end md:flex">
          <button
            onClick={handleToggle}
            data-testid="sidebar-toggle"
            aria-label="Collapse"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/5 bg-slate-950 text-slate-400 transition-all hover:bg-slate-800 hover:text-white mx-auto"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </aside>
    </>
  );
};
