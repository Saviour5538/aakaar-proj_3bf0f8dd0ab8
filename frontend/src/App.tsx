import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import FileUploadList from './pages/FileUploadList';
import FileUploadForm from './pages/FileUploadForm';
import ChunkingStrategyList from './pages/ChunkingStrategyList';
import ChunkingStrategyForm from './pages/ChunkingStrategyForm';
import UserInterfaceList from './pages/UserInterfaceList';
import UserInterfaceForm from './pages/UserInterfaceForm';
import DatabaseIntegrationList from './pages/DatabaseIntegrationList';
import DatabaseIntegrationForm from './pages/DatabaseIntegrationForm';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="file-uploads" element={<FileUploadList />} />
            <Route path="file-uploads/new" element={<FileUploadForm />} />
            <Route path="file-uploads/:id/edit" element={<FileUploadForm />} />
            <Route path="chunking-strategies" element={<ChunkingStrategyList />} />
            <Route path="chunking-strategies/new" element={<ChunkingStrategyForm />} />
            <Route path="chunking-strategies/:id/edit" element={<ChunkingStrategyForm />} />
            <Route path="user-interfaces" element={<UserInterfaceList />} />
            <Route path="user-interfaces/new" element={<UserInterfaceForm />} />
            <Route path="user-interfaces/:id/edit" element={<UserInterfaceForm />} />
            <Route path="database-integrations" element={<DatabaseIntegrationList />} />
            <Route path="database-integrations/new" element={<DatabaseIntegrationForm />} />
            <Route path="database-integrations/:id/edit" element={<DatabaseIntegrationForm />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;