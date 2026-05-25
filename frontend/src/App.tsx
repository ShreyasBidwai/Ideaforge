import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/layout/ProtectedRoute";
import Approvals from "./pages/Approvals";
import Discovery from "./pages/Discovery";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ProblemLibrary from "./pages/ProblemLibrary";
import SolutionWorkspace from "./pages/SolutionWorkspace";

const App: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected Routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/discovery" element={<Discovery />} />
        <Route path="/library" element={<ProblemLibrary />} />
        <Route path="/workspace/:problemId" element={<SolutionWorkspace />} />
        <Route path="/approvals" element={<Approvals />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
