import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./styles/index.css";
import { AuthProvider } from "./context/AuthContext";
import { AppLayout } from "./layouts/AppLayout";
import { LandingPage } from "./pages/LandingPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LiveMonitoringPage } from "./pages/LiveMonitoringPage";
import { ZonesPage } from "./pages/ZonesPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { EvidencePage } from "./pages/EvidencePage";
import { AssistantPage } from "./pages/AssistantPage";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Navigate to="/dashboard" replace />} />
          <Route path="/signup" element={<Navigate to="/dashboard" replace />} />
          <Route path="/forgot-password" element={<Navigate to="/dashboard" replace />} />
          <Route path="/reset-password" element={<Navigate to="/dashboard" replace />} />
          <Route path="/verify-email" element={<Navigate to="/dashboard" replace />} />
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/live-monitoring" element={<LiveMonitoringPage />} />
            <Route path="/zones" element={<ZonesPage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
