import { Routes, Route, Navigate } from 'react-router-dom';
import { useStore } from './stores/useStore';
import Layout from './layouts/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import InboxPage from './pages/InboxPage';
import ConversationPage from './pages/ConversationPage';
import KnowledgePage from './pages/KnowledgePage';
import GapsPage from './pages/GapsPage';
import EvaluationPage from './pages/EvaluationPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ModelPage from './pages/ModelPage';
import SettingsPage from './pages/SettingsPage';
import UploadPage from './pages/UploadPage';
import ToastContainer from './components/ToastContainer';
import CommandPalette from './components/CommandPalette';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useStore(s => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="inbox" element={<InboxPage />} />
          <Route path="conversation/:id" element={<ConversationPage />} />
          <Route path="knowledge" element={<KnowledgePage />} />
          <Route path="gaps" element={<GapsPage />} />
          <Route path="evaluation" element={<EvaluationPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="model" element={<ModelPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
      <ToastContainer />
      <CommandPalette />
    </>
  );
}
