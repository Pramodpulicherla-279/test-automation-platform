import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import TestScreen from "./components/TestScreen/TestScreen";
import JiraHistory from "./components/JiraHistory/JiraHistory";
import APIBatchTester from "./components/APIBatchTester/APIBatchTester";
import Sidebar from "./components/Sidebar/Sidebar";
import AdvancedApiTester from "./components/ApiTester/AdvancedApiTester";
import './App.css';

function Layout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="app-layout-content">
        <Outlet />
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<Layout />}>
          <Route index element={<TestScreen />} />
          <Route path="jira-history" element={<JiraHistory />} />
          <Route path="api-tester" element={<AdvancedApiTester />} />
          <Route path="api-batch" element={<APIBatchTester />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />

      </Routes>
    </BrowserRouter>
  );
}

export default App;