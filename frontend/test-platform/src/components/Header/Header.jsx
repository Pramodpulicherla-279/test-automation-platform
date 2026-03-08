
import React, { useState, useEffect, useRef } from 'react';

import { Activity, Server, Smartphone } from "lucide-react";
import { ReadyState } from "react-use-websocket";

export default function Header({
  appIcon,
  appTitle,
  isDeviceConnected,
  readyState,
  appiumStatus,
  uiIssuesOpen,
  uiIssuesLoading,
  onToggleUiIssues,
}) {

  return (
    <header className="app-header">
      {appIcon ? (
        <div className="app-header-left">
          <img src={appIcon} alt="App Logo" className="app-logo" />
          <h1>{appTitle || "Android App"}</h1>
        </div>
      ) : (
        <div className="w-16 h-16 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-500" />
      )}

      {/* <div>
        <h1 className="brand-title">TAP / Android</h1>
        <p className="brand-subtitle">Test Automation Platform • Live Profiler</p>
      </div> */}

      <div className="status-cont">
        <div className="status-box">
          <div className="system-status">
            <Smartphone
              size={18}
              color={isDeviceConnected ? "#4ade80" : "#ef4444"}
              style={{ marginRight: "6px" }}
            />
            <span style={{ color: isDeviceConnected ? "#4ade80" : "#ef4444" }}>
              {isDeviceConnected ? "Device Connected" : "No Device"}
            </span>
          </div>

          <div className="system-status">
            <Server
              size={18}
              color={readyState === ReadyState.OPEN ? "#4ade80" : "#ef4444"}
              style={{ marginRight: "6px" }}
            />
            <span style={{ color: readyState === ReadyState.OPEN ? "#4ade80" : "#ef4444" }}>
              {readyState === ReadyState.OPEN ? "Server Connected" : "Offline"}
            </span>
          </div>

          <div className="system-status" style={{ borderRight: "none" }}>
            <Activity
              size={18}
              color={appiumStatus === "running" ? "#4ade80" : "#94a3b8"}
              style={{ marginRight: "6px" }}
            />
            <span style={{ color: appiumStatus === "running" ? "#4ade80" : "#94a3b8" }}>
              Appium {appiumStatus === "running" ? "Active" : "Off"}
            </span>
          </div>
        </div>

        <button
          onClick={onToggleUiIssues}
          disabled={uiIssuesLoading}
          className="view-UI-button"
          style={{
            padding: "8px 12px",
            backgroundColor: "#334155",
            color: "#e2e8f0",
            border: "1px solid #475569",
          }}
          title={uiIssuesOpen ? "Close UI Screenshot Issues screen" : "Open UI Screenshot Issues screen"}
        >
          {uiIssuesOpen ? "Close UI Issues" : "View UI Issues"}
        </button>
      </div>
    </header>
  );
}