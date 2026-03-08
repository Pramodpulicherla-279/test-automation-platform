import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import TestScreen  from "./components/TestScreen/TestScreen";
import MainScreen from "./components/MainScreen/MainScreen";
import JiraHistory from "./components/JiraHistory/JiraHistory";
import Sidebar from "./components/Sidebar/Sidebar";
import './App.css'; // Import the new CSS file


const WS_URL = 'ws://localhost:8000/ws/test-status';
const API_URL = 'http://localhost:8000';

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
        <Route element={<Layout />}>
          <Route path="/" element={<TestScreen />} />
          <Route path="/jira-history" element={<JiraHistory />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;