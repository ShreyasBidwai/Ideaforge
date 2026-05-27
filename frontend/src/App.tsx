import React, { useEffect, lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/layout/ProtectedRoute";
import AppShell from "./components/layout/AppShell";
import LoadingSpinner from "./components/ui/LoadingSpinner";
import { ToastContainer } from "./components/ui/Toast";
import { useAuthStore } from "./stores/authStore";

// Lazy-loaded pages
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Discovery = lazy(() => import("./pages/Discovery"));
const ProblemLibrary = lazy(() => import("./pages/ProblemLibrary"));
const SolutionWorkspace = lazy(() => import("./pages/SolutionWorkspace"));
const Evaluation = lazy(() => import("./pages/Evaluation"));
const Approvals = lazy(() => import("./pages/Approvals"));
const BuildDashboard = lazy(() => import("./pages/BuildDashboard"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));

const App: React.FC = () => {
  const { accessToken, fetchCurrentUser, logout } = useAuthStore();

  useEffect(() => {
    if (accessToken) {
      fetchCurrentUser().catch(() => {
        logout();
      });
    }
  }, [accessToken, fetchCurrentUser, logout]);

  return (
    <>
      <Suspense fallback={<LoadingSpinner message="Loading..." />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/discovery" element={<Discovery />} />
              <Route path="/library" element={<ProblemLibrary />} />
              <Route path="/workspace/:problemId" element={<SolutionWorkspace />} />
              <Route path="/evaluation/:problemId" element={<Evaluation />} />
              <Route path="/approvals" element={<Approvals />} />
              <Route path="/projects/:projectId/build" element={<BuildDashboard />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
      <ToastContainer />
    </>
  );
};

export default App;
