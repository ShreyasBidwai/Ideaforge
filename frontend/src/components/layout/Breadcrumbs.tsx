import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

export const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  const pathnames = location.pathname.split("/").filter((x) => x);

  const getBreadcrumbLabel = (segment: string, index: number) => {
    if (segment === "discovery") return "Discovery";
    if (segment === "library") return "Problem Library";
    if (segment === "workspace") return "Solution Workspace";
    if (segment === "approvals") return "Approvals";
    if (segment === "projects") return "Projects";
    if (segment === "build") return "Build";
    if (segment === "documents") return "Documents";
    if (segment === "edit") return "Edit Document";
    // Check if previous segment is workspace, then this segment is the problem ID
    if (index > 0 && pathnames[index - 1] === "workspace") {
      return `Problem #${segment.slice(0, 8)}`;
    }
    // Check if previous segment is projects, then this segment is the project ID / name
    if (index > 0 && pathnames[index - 1] === "projects") {
      return `Project #${segment.slice(0, 8)}`;
    }
    // Check if previous segment is documents, then this segment is the doc ID
    if (index > 0 && pathnames[index - 1] === "documents") {
      return `Document #${segment.slice(0, 8)}`;
    }
    return segment.charAt(0).toUpperCase() + segment.slice(1);
  };

  return (
    <nav className="flex items-center space-x-2 text-sm text-slate-400 font-medium">
      <Link
        to="/"
        className="flex items-center hover:text-white transition-colors"
      >
        <Home size={16} className="mr-1" />
        <span>Home</span>
      </Link>
      {pathnames.length === 0 && (
        <>
          <ChevronRight size={14} className="text-slate-600" />
          <span className="text-slate-200">Dashboard</span>
        </>
      )}
      {pathnames.map((segment, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join("/")}`;
        const isLast = index === pathnames.length - 1;
        const label = getBreadcrumbLabel(segment, index);

        return (
          <React.Fragment key={routeTo}>
            <ChevronRight size={14} className="text-slate-600" />
            {isLast ? (
              <span className="text-slate-200">{label}</span>
            ) : (
              <Link
                to={routeTo}
                className="hover:text-white transition-colors"
              >
                {label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};
