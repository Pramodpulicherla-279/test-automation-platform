/**
 * App.jsx
 *
 * Shared state flow:
 *   JiraHistoryContext holds the history array.
 *   IssuePanel (inside TestScreen) calls addToJiraHistory() when:
 *     - user clicks Create  → type: "created"  → shows in Assigned tab
 *     - user clicks Remove  → type: "removed"  → shows in Unassigned tab
 *   JiraHistory screen reads the history from context.
 */

import React, { createContext, useContext, useState, useCallback } from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";

import TestScreen   from "./components/TestScreen/TestScreen";
import JiraHistory  from "./components/JiraHistory/JiraHistory";
import Sidebar      from "./components/Sidebar/Sidebar";
import APIMatrixTester from "./components/APIMatrixTester/APIMatrixTester";
import APIBatchTester from "./components/APIBatchTester/APIBatchTester";
import "./App.css";

/* ─── Shared Jira History Context ─────────────────────────────────────────── */
export const JiraHistoryContext = createContext({
  history:           [],
  addToJiraHistory:  () => {},
});

export function useJiraHistory() {
  return useContext(JiraHistoryContext);
}

function JiraHistoryProvider({ children }) {
  const [history, setHistory] = useState([]);

  const addToJiraHistory = useCallback((entry) => {
    // entry shape: { type: "created"|"removed", issueId, title,
    //               jiraUrl, module, priority, developer,
    //               savedAt, ... }
    setHistory((prev) => {
      // Deduplicate by issueId for "created" entries
      if (entry.type === "created" && entry.issueId) {
        const exists = prev.some(
          (h) => h.type === "created" && h.issueId === entry.issueId
        );
        if (exists) return prev;
      }
      return [entry, ...prev];
    });
  }, []);

  return (
    <JiraHistoryContext.Provider value={{ history, addToJiraHistory }}>
      {children}
    </JiraHistoryContext.Provider>
  );
}

/* ─── Layout ──────────────────────────────────────────────────────────────── */
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

/* ─── TestScreen wrapper — injects onHistoryUpdate into IssuePanel ─────────
 *
 * TestScreen renders IssuePanel internally.
 * We pass addToJiraHistory down so IssuePanel can call it.
 *
 * If TestScreen already accepts an `onHistoryUpdate` prop, this just works.
 * If it doesn't yet, see the note below — you need to add one line to TestScreen.
 * ─────────────────────────────────────────────────────────────────────────── */
function TestScreenWithHistory() {
  const { addToJiraHistory } = useJiraHistory();
  return <TestScreen onHistoryUpdate={addToJiraHistory} />;
}

/* ─── JiraHistory wrapper — reads from context ───────────────────────────── */
function JiraHistoryWithContext() {
  const { history } = useJiraHistory();
  return <JiraHistory issuePanelHistory={history} />;
}

/* ─── App ─────────────────────────────────────────────────────────────────── */
function App() {
  return (
    <JiraHistoryProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/"             element={<TestScreenWithHistory />} />
            <Route path="/jira-history" element={<JiraHistoryWithContext />} />
            <Route path="/api-matrix"   element={<APIMatrixTester />} />
            <Route path="/api-batch"    element={<APIBatchTester />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </JiraHistoryProvider>
  );
}

export default App;