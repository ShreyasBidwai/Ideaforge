import React, { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/layout/ProtectedRoute";
import AppShell from "./components/layout/AppShell";
import Approvals from "./pages/Approvals";
import Discovery from "./pages/Discovery";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ProblemLibrary from "./pages/ProblemLibrary";
import SolutionWorkspace from "./pages/SolutionWorkspace";
import Evaluation from "./pages/Evaluation";
import { ToastContainer } from "./components/ui/Toast";
import { useAuthStore } from "./stores/authStore";

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
          </Route>
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ToastContainer />
    </>
  );
};

export default App;
