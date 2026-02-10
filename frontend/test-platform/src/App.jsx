import React, { useState, useEffect, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Play, Terminal, Activity, CheckCircle, Circle, AlertCircle, Cpu, Smartphone, Server, Maximize2, Minimize2 } from 'lucide-react';

import './App.css'; // Import the new CSS file

const WS_URL = 'ws://localhost:8000/ws/test-status';
const API_URL = 'http://localhost:8000';

// --- CONFIGURATION: App Variants & Modules ---
const APP_VARIANTS = {
  FARMER: {
    id: "regular_farmer",
    label: "Krishivaas Farmer (Regular)",
    modules: [
      { name: 'Login', path: 'tests/test_cases/regular_farmer_test_cases/test_login_pytest.py' },
      { name: 'Dashboard', path: 'tests/test_cases/regular_farmer_test_cases/TestOnboarding.py' },
      { name: 'Add Updates', path: 'tests/farmer/test_updates.py' },
    ]
  },
  CLIENT: {
    id: "regular_client",
    label: "Krishivaas Client (Regular)",
    modules: [
      { name: 'Login', path: 'tests/test_cases/regular_client_test_cases/login_pytest.py' },
      { name: 'Marketplace', path: 'tests/client/test_marketplace.py' },
      { name: 'Cart', path: 'tests/client/test_cart.py' },
    ]
  },
  STATE_FARMER: {
    id: "state_farmer",
    label: "State Farmer App",
    modules: [
      { name: 'Login', path: 'tests/state_farmer/test_login.py' },
      { name: 'Schemes', path: 'tests/state_farmer/test_schemes.py' },
    ]
  },
  STATE_CLIENT: {
    id: "state_client",
    label: "State Client App",
    modules: [
      { name: 'Login', path: 'tests/state_client/test_login.py' },
      { name: 'Tenders', path: 'tests/state_client/test_tenders.py' },
    ]
  }
};

// --- COMPONENT: Module Flow Status ---
const ModuleFlow = ({ modules, isRunning, onToggleModule }) => {
  return (
    <div className="dashboard-card module-card">
      <h3 className="card-title">
        <Activity size={20} className="icon-blue" /> Module Flow Status
      </h3>
      <div className="module-list">
        {modules.map((mod, idx) => {
          let statusClass = "status-pending";
          let icon = <Circle size={16} />;

          if (mod.status === 'completed') {
            statusClass = "status-success";
            icon = <CheckCircle size={16} />;
          } else if (mod.status === 'running') {
            statusClass = "status-running";
            icon = <Activity size={16} className="icon-pulse" />;
          } else if (mod.status === 'failed') {
            statusClass = "status-failed";
            icon = <AlertCircle size={16} />;
          }

          // Interactive classes only when not running
          const interactiveClass = !isRunning ? "clickable-module" : "";

          return (
            <div key={idx} className={`module-item ${statusClass} ${interactiveClass}`}
            onClick={() => !isRunning && onToggleModule(idx)}
            style={{
                cursor: !isRunning ? 'pointer' : 'default',
              }}>
              {/* Show checkbox only if NOT running */}
              {!isRunning ? (
                <input
                  type="checkbox"
                  checked={!!mod.isSelected}
                  // Stop propagation so clicking checkbox doesn't trigger row click twice
                  onClick={(e) => e.stopPropagation()} 
                  onChange={() => onToggleModule(idx)}
                  className="mr-2 cursor-pointer"
                  style={{ marginRight: '0px' }}
                />
              ) : (
                // Show status icon if running or if selected
                mod.isSelected ? icon : <Circle size={16} className="text-gray-500" />
              )}

              <span className={`module-name ${!mod.isSelected && !isRunning ? 'opacity-50' : ''}`}>
                {mod.name}
              </span>
              {mod.status === 'running' && <span className="status-label">Testing...</span>}
              {mod.status === 'completed' && <span className="status-label" style={{ color: '#22c55e' }}>Completed</span>}
              {mod.status === 'failed' && <span className="status-label" style={{ color: '#ef4444' }}>Failed</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// --- COMPONENT: Live Metrics Chart ---
const MetricsChart = ({ data }) => {
  return (
    <div className="dashboard-card chart-card">
      <h3 className="card-title">
        <Cpu size={20} className="icon-purple" /> Live Profiler Metrics
      </h3>
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="time" hide />
            <YAxis yAxisId="left" stroke="#94a3b8" label={{ value: 'CPU %', angle: -90, position: 'insideLeft' }} domain={[0, 100]} />
            <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" label={{ value: 'MB', angle: 90, position: 'insideRight' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#e2e8f0' }}
              itemStyle={{ color: '#e2e8f0' }}
            />
            <Line yAxisId="left" type="monotone" dataKey="cpu" stroke="#38bdf8" strokeWidth={2} dot={false} animationDuration={300} />
            <Line yAxisId="right" type="monotone" dataKey="memory" stroke="#c084fc" strokeWidth={2} dot={false} animationDuration={300} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// --- COMPONENT: Log Console ---
const LogConsole = ({ logs, statusMode = 'idle' }) => {
  const endRef = useRef(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isFullScreen, setIsFullScreen] = useState(false);

  const filteredLogs = logs.filter((log) => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      log.message.toLowerCase().includes(q) ||
      log.type.toLowerCase().includes(q) ||
      String(log.time).toLowerCase().includes(q)
    );
  });

  const normalizedSearch = searchTerm.toLowerCase().trim();

  const matchesSearch = (log) => {
    if (!normalizedSearch) return false;
    return (
      log.message.toLowerCase().includes(normalizedSearch) ||
      log.type.toLowerCase().includes(normalizedSearch) ||
      String(log.time).toLowerCase().includes(normalizedSearch)
    );
  };

  // Styles for the status bar
  const getBarStyle = () => {
    const baseStyle = {
      height: '4px',
      flexGrow: 1,
      margin: '0 15px',
      borderRadius: '2px',
      transition: 'all 0.3s ease',
      opacity: statusMode === 'idle' ? 0.2 : 1,
      backgroundColor: statusMode === 'idle' ? '#475569' : '#fff',
    };

    if (statusMode === 'running') {
      return {
        ...baseStyle,
        background: 'linear-gradient(90deg, #3b82f633 0%, #3b82f6 50%, #3b82f633 100%)',
        backgroundSize: '200% 100%',
        animation: 'gradientLoad 2s linear infinite',
      };
    } else if (statusMode === 'failure') {
      return {
        ...baseStyle,
        backgroundColor: '#ef4444',
        boxShadow: '0 0 8px #ef444466',
        animation: 'blinkRed 1.5s infinite',
      };
    } else if (statusMode === 'success') {
      return {
        ...baseStyle,
        backgroundColor: '#22c55e',
        boxShadow: '0 0 8px #22c55e66',
        animation: 'blinkGreen 1.5s infinite',
      };
    }
    return baseStyle;
  };

  return (
    <div className={`log-console ${isFullScreen ? 'full-screen' : ''}`}>
      <style>{`
        @keyframes gradientLoad {
          0% { background-position: 100% 0; }
          100% { background-position: -100% 0; }
        }
        @keyframes blinkRed {
          0%, 100% { opacity: 1; box-shadow: 0 0 8px #ef444466; }
          50% { opacity: 0.4; box-shadow: none; }
        }
        @keyframes blinkGreen {
          0%, 100% { opacity: 1; box-shadow: 0 0 8px #22c55e66; }
          50% { opacity: 0.4; box-shadow: none; }
        }
      `}</style>

      <div className="console-header-row">
        <h3 className="console-header">
          <Terminal size={14} /> LIVE LOGS CONSOLE
        </h3>
        <div style={getBarStyle()} />
        {/* Search bar */}
        <div className="log-search">
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="text-input"
          />
        </div>
        <button
          onClick={() => setIsFullScreen(!isFullScreen)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            marginLeft: '8px',
            color: '#94a3b8',
            display: 'flex',
            alignItems: 'center',
            padding: '4px'
          }}
          title={isFullScreen ? "Exit Full Screen" : "Full Screen"}
        >
          {isFullScreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
        </button>
      </div>
      <div className="console-body">
        {logs.map((log, i) => {
          const isMatch = matchesSearch(log);
          return (
            <div
              key={i}
              className={`log-line ${log.type.toLowerCase()} ${isMatch ? 'log-line-highlight' : ''
                }`}
            >
              <span className="timestamp">[{log.time}]</span>
              <span className="message">{log.message}</span>
            </div>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
};

// --- MAIN APP COMPONENT ---
function App() {
  const loadState = (key, fallback) => {
    try {
      const saved = sessionStorage.getItem(key);
      return saved ? JSON.parse(saved) : fallback;
    } catch (e) {
      return fallback;
    }
  };
  const [apkUrl, setApkUrl] = useState(() => loadState('apkUrl', ''));
  const [isRunning, setIsRunning] = useState(() => loadState('isRunning', false));
  const [isDownloading, setIsDownloading] = useState(false);
  // const [logs, setLogs] = useState([]);
  // Load logs, but limit history to prevent quota errors
  const [logs, setLogs] = useState(() => loadState('logs', []));
  const [metrics, setMetrics] = useState([]);
  const [appIcon, setAppIcon] = useState(null);
  const [appTitle, setAppTitle] = useState('');
  const [isDeviceConnected, setIsDeviceConnected] = useState(false);
  const [appiumStatus, setAppiumStatus] = useState('stopped');
  const [showStopPopup, setShowStopPopup] = useState(false);
  const [selectedAppKey, setSelectedAppKey] = useState(() => loadState('selectedAppKey', 'FARMER'));
  // Track previous key to prevent module reset on refresh
  const prevAppKeyRef = useRef(selectedAppKey);
  // Initialize modules based on default selection or storage
  const [modules, setModules] = useState(() => {
    const saved = sessionStorage.getItem('modules');
    if (saved) return JSON.parse(saved);
    // Use the potentially loaded key, fallback to FARMER if invalid
    const variant = APP_VARIANTS[selectedAppKey] || APP_VARIANTS['FARMER'];
    return variant.modules.map(m => ({
      ...m,
      status: 'pending',
      isSelected: true
    }));
  });

  const [existingApks, setExistingApks] = useState([]);
  const [selectedApk, setSelectedApk] = useState(() => loadState('selectedApk', ''));
  const reportWindowRef = useRef(null);
  const [hasOpenedReport, setHasOpenedReport] = useState(false);

  // Save specific state to sessionStorage whenever it changes
  useEffect(() => {
    sessionStorage.setItem('apkUrl', JSON.stringify(apkUrl));
    sessionStorage.setItem('isRunning', JSON.stringify(isRunning));
    sessionStorage.setItem('selectedAppKey', JSON.stringify(selectedAppKey));
    sessionStorage.setItem('modules', JSON.stringify(modules));
    sessionStorage.setItem('selectedApk', JSON.stringify(selectedApk));
    // Limit persisted logs to last 200 to avoid storage quota limits
    sessionStorage.setItem('logs', JSON.stringify(logs.slice(-200)));
  }, [apkUrl, isRunning, selectedAppKey, modules, selectedApk, logs]);

  // Helper to determine status bar state
  const getConsoleStatus = () => {
    if (isRunning) return 'running';
    
    const active = modules.filter(m => m.isSelected);
    // If no modules or all correspond to 'pending', we are idle/start
    if (active.length === 0) return 'idle';

    // If any failed -> failure
    if (active.some(m => m.status === 'failed')) return 'failure';

    // This handles cases where some modules might be skipped (staying 'pending')
    const hasCompleted = active.some(m => m.status === 'completed' || m.status === 'passed');
    const hasRunning = active.some(m => m.status === 'running');

    // If all completed -> success
    if (hasCompleted && !hasRunning) return 'success';
    
    return 'idle';
  };

  // --- Update modules when App Type changes ---
  useEffect(() => {
    // Only reset modules if the user ACTUALLY changed the dropdown
    // NOT on initial render/refresh (where prev == current)
    if (prevAppKeyRef.current !== selectedAppKey) {
      setModules(APP_VARIANTS[selectedAppKey].modules.map(m => ({
        ...m,
        status: 'pending',
        isSelected: true
      })));
      prevAppKeyRef.current = selectedAppKey;
    }
  }, [selectedAppKey]);

  const toggleModuleSelection = (index) => {
    if (isRunning) return;
    setModules(prev => prev.map((m, i) => i === index ? { ...m, isSelected: !m.isSelected } : m));
  };

  const updateModuleStatus = (moduleName, newStatus) => {
    setModules(prev =>
      prev.map(m =>
        m.name.toLowerCase() === moduleName.toLowerCase()
          ? { ...m, status: newStatus }
          : m
      )
    );
  };

  const { lastJsonMessage, sendMessage, readyState } = useWebSocket(WS_URL, {
    shouldReconnect: () => true,
    onMessage: (event) => {
      const data = JSON.parse(event.data);
      handleIncomingData(data);
    }
  });

  const openOrNavigateReport = (url) => {
    if (!url || hasOpenedReport) return;
    window.open(url, '_blank', 'noopener,noreferrer');
    setHasOpenedReport(true);
  };

  const handleIncomingData = (data) => {
    if (data.type === 'LOG') {
      const { message, status } = data.payload || {};

      // Handle PROGRESS updates by replacing the last line if it's also a progress line
      if (status === 'PROGRESS') {
        setLogs(prev => {
          if (prev.length > 0 && prev[prev.length - 1].type === 'PROGRESS') {
            // Replace the last log entry
            const newLogs = [...prev];
            newLogs[newLogs.length - 1] = { 
              time: new Date().toLocaleTimeString(), 
              message, 
              type: status 
            };
            return newLogs;
          }
          // Otherwise append
          return [...prev, { time: new Date().toLocaleTimeString(), message, type: status }];
        });
        return; // Skip the rest of the logic for progress
      }
      
      setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), message, type: status || 'INFO' }]);

      // FAILSAFE: Force stop running state if we see end-of-run log messages
      if (message && (
        message.includes("Allure HTML report generated") ||
        message.includes("Skipping report generation") ||
        message.includes("Test execution interrupted") ||
        message.includes("Test process terminated")
      )) {
        setIsRunning(false);
      }

    } else if (data.type === 'MODULE') {
      const { module, status, message } = data.payload || {};
      if (module && status) {
        setModules(prev => {
          const updated = prev.map(m =>
            m.name.toLowerCase() === module.toLowerCase() ? { ...m, status } : m
          );

          // FIX: Only stop running if NO modules are running AND NO selected modules are pending
          const hasRunning = updated.some(m => m.status === 'running');
          const hasPending = updated.some(m => m.status === 'pending' && m.isSelected);

          if (!hasRunning && !hasPending) {
            setIsRunning(false);
          }
          return updated;
        });

        if (message) {
          setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), message: `[${module}] ${message}`, type: status.toUpperCase() }]);
        }
      }
    } else if (data.type === 'RUN_COMPLETE') {
      setIsRunning(false);
      // if (!hasOpenedReport && data.payload?.report_url) {
      //   window.open(data.payload.report_url, '_blank', 'noopener,noreferrer');
      //   setHasOpenedReport(true);
      // }
    }
  };

  const handleRunTest = async () => {
    if (appiumStatus !== 'running') {
      alert("Appium Server is not running. Please start the server using the 'Start Server' button.");
      return;
    }

    if (!apkUrl && !selectedApk) {
      alert("Please enter a Google Drive URL or select an existing APK!");
      return;
    }

    const testsToRun = modules
      .filter(m => m.isSelected)
      .map(m => ({ name: m.name, path: m.path }));

    if (testsToRun.length === 0) {
      alert("Please select at least one module to run.");
      return;
    }

    setHasOpenedReport(false);
    setModules(prev => prev.map(m => ({ ...m, status: 'pending' })));
    setIsRunning(true);
    setIsDownloading(!!apkUrl);
    setLogs([]);

    // --- NEW: Add initial log ---
    const appLabel = APP_VARIANTS[selectedAppKey].label;
    handleIncomingData({
      type: 'LOG',
      payload: {
        message: `Initializing ${appLabel} test with ${testsToRun.length} modules...`,
        status: 'INFO'
      }
    });

    try {
      // --- NEW: Send app_type in payload ---
      const payload = {
        tests_to_run: testsToRun,
        app_type: APP_VARIANTS[selectedAppKey].id
      };

      let endpoint = selectedApk ? '/start-test-existing' : '/start-test';
      let body = selectedApk
        ? { ...payload, apk_name: selectedApk }
        : { ...payload, url: apkUrl };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (data.app_icon) setAppIcon(data.app_icon);
      if (data.app_name) setAppTitle(data.app_name);

      if (!response.ok) throw new Error(data.detail || 'Failed to start test');

      handleIncomingData({
        type: 'LOG',
        payload: { message: `Backend accepted job. APK Path: ${data.apk_path}`, status: 'SUCCESS' }
      });

    } catch (error) {
      console.error("Error starting test:", error);
      handleIncomingData({
        type: 'LOG',
        payload: { message: `Error: ${error.message}`, status: 'FAILED' }
      });
      setIsRunning(false);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleStopTest = async () => {
    try {
      await fetch(`${API_URL}/stop-test`, { method: 'POST' });
    } catch (e) { console.error(e); }
    setIsRunning(false);
    setIsDownloading(false);
    handleIncomingData({ type: 'LOG', payload: { message: 'Test stopped by user.', status: 'FAILED' } });
    setShowStopPopup(true);
  };

    const handleGenerateReport = async () => {
    setShowStopPopup(false);
    try {
       await fetch(`${API_URL}/api/generate-report`, { method: 'POST' });
       handleIncomingData({ type: 'LOG', payload: { message: 'Generating partial report...', status: 'INFO' } });
    } catch (e) {
       console.error("Failed to generate report", e);
    }
  };

   // --- NEW: Reset Handler ---
  const handleReset = () => {
    // 1. Reset UI State
    setIsRunning(false);
    setApkUrl('');
    setSelectedApk('');
    setLogs([]);
    // Reset module statuses to pending, keep selection
    setModules(prev => prev.map(m => ({ ...m, status: 'pending' })));

    // 2. Clear Session Storage
    sessionStorage.removeItem('apkUrl');
    sessionStorage.removeItem('selectedApk');
    sessionStorage.removeItem('logs');
    sessionStorage.removeItem('modules');
    sessionStorage.removeItem('isRunning');
  };

  // --- NEW: Appium Handlers ---
  const checkAppiumStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/appium/status`);
      const data = await res.json();
      setAppiumStatus(data.status);
    } catch (e) {
      setAppiumStatus('stopped');
    }
  };

  const toggleAppium = async () => {
    try {
      if (appiumStatus === 'running') {
        await fetch(`${API_URL}/api/appium/stop`, { method: 'POST' });
        handleIncomingData({ type: 'LOG', payload: { message: 'Stopping Appium Server...', status: 'INFO' } });
      } else {
        await fetch(`${API_URL}/api/appium/start`, { method: 'POST' });
        handleIncomingData({ type: 'LOG', payload: { message: 'Starting Appium Server...', status: 'INFO' } });
      }
      // Give it a moment to change state then check
      setTimeout(checkAppiumStatus, 1000);
    } catch (error) {
      console.error("Failed to toggle Appium", error);
    }
  };

  // Poll device & Load APKs
  useEffect(() => {
    const checkDevice = async () => {
      try {
        const res = await fetch(`${API_URL}/device-status`);
        const data = await res.json();
        setIsDeviceConnected(!!data.connected);
      } catch (e) { setIsDeviceConnected(false); }
    };

    const loadApks = async () => {
      try {
        const res = await fetch(`${API_URL}/api/apk-list`);
        const data = await res.json();
        setExistingApks(data.apks || []);
      } catch (e) { }
    };

    loadApks();
    checkDevice();
    checkAppiumStatus(); 
    const id = setInterval(() => {
      checkDevice();
      checkAppiumStatus();
    }, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        {appIcon ? (
          <div className="app-header-left">
            <img
              src={appIcon}
              alt="App Logo"
              className="app-logo"
            />
            <h1>{appTitle || 'Android App'}</h1>
          </div>
        ) : (
          // Fallback placeholder if no icon yet
          <div className="w-16 h-16 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-500">
            {/* <span className="text-xs">No Icon</span> */}
          </div>
        )}
        <div>
          <h1 className="brand-title">TAP / Android</h1>
          <p className="brand-subtitle">Test Automation Platform • Live Profiler</p>
        </div>
        <div className='status-box'>
          <div className="system-status">
            <Smartphone
              size={18}
              color={isDeviceConnected ? '#4ade80' : '#ef4444'}
              style={{ marginRight: '6px' }}
            />
            <span style={{ color: isDeviceConnected ? '#4ade80' : '#ef4444' }}>
              {isDeviceConnected ? 'Device Connected' : 'No Device'}
            </span>
          </div>
          <div className="system-status">
            <Server
              size={18}
              color={readyState === ReadyState.OPEN ? '#4ade80' : '#ef4444'}
              style={{ marginRight: '6px' }}
            />
            <span style={{ color: readyState === ReadyState.OPEN ? '#4ade80' : '#ef4444' }}>
              {readyState === ReadyState.OPEN ? 'Server Connected' : 'Offline'}
            </span>
          </div>
          <div className="system-status">
            <Activity
              size={18}
              color={appiumStatus === 'running' ? '#4ade80' : '#94a3b8'}
              style={{ marginRight: '6px' }}
            />
            <span style={{ color: appiumStatus === 'running' ? '#4ade80' : '#94a3b8' }}>
              Appium {appiumStatus === 'running' ? 'Active' : 'Off'}
            </span>
          </div>
        </div>
      </header>

      {showStopPopup && (
        <div style={{
          position: 'fixed', top:'30%', left: 0, right: 0, 
          // backgroundColor: 'rgba(0,0,0,0.7)',
          // height: '50vh',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="dashboard-card" style={{ width: '400px', padding: '24px', border: '1px solid #ebebeb' }}>
            <h3 style={{ marginTop: 0, color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle color="#f59e0b" /> Test Stopped
            </h3>
            <p style={{ color: '#94a3b8', margin: '16px 0 24px 0' }}>
              Tests were stopped manually. Do you want to generate and view the partial report for the executed tests?
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                onClick={() => setShowStopPopup(false)}
                style={{
                  padding: '8px 16px', borderRadius: '6px', cursor: 'pointer',
                  backgroundColor: 'transparent', border: '1px solid #475569', color: '#333'
                }}
              >
                No, Close
              </button>
              <button
                onClick={handleGenerateReport}
                style={{
                  padding: '8px 16px', borderRadius: '6px', cursor: 'pointer',
                  backgroundColor: '#3b82f6', border: 'none', color: 'white', fontWeight: '500'
                }}
              >
                Yes, Generate Report
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        {/* Panel 1: Controls */}
        <div className="dashboard-card control-panel">
          {/* <h2 className="card-title">Test Execution</h2> */}
          {/* --- NEW: Appium Control Row --- */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            paddingBottom: '15px', 
            marginBottom: '15px',
            borderBottom: '1px solid #334155' 
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ 
                width: '10px', 
                height: '10px', 
                borderRadius: '50%', 
                backgroundColor: appiumStatus === 'running' ? '#4ade80' : '#ef4444',
                boxShadow: appiumStatus === 'running' ? '0 0 8px #4ade80' : 'none'
              }}></div>
              <span className="input-label" style={{ marginBottom: 0 }}>Appium Server</span>
            </div>
            
            <button
              onClick={toggleAppium}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: '1px solid #CBD5E1',
                backgroundColor: appiumStatus === 'running' ? '#1e293b' : '#0f172a',
                color: appiumStatus === 'running' ? '#ef4444' : '#4ade80',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: '600',
                transition: 'all 0.2s'
              }}
            >
              {appiumStatus === 'running' ? 'Stop Server' : 'Start Server'}
            </button>
          </div>
          {/* App Selector */}
          <div className="input-group mb-4">
            <label className="input-label">Select Application</label>
            <div className="select-wrapper">
              <select
                className="text-input"
                value={selectedAppKey}
                onChange={(e) => setSelectedAppKey(e.target.value)}
                disabled={isRunning}
              >
                {Object.entries(APP_VARIANTS).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="input-group">
            <label className="input-label">APK Source (Drive URL)</label>
            <input
              type="text"
              placeholder="https://drive.google.com/..."
              value={apkUrl}
              onChange={(e) => { setApkUrl(e.target.value); if (e.target.value) setSelectedApk(''); }}
              className="text-input"
              disabled={isRunning || !!selectedApk}
            />
          </div>

          <div className="input-group mt-2">
            <label className="input-label">OR Select Existing APK</label>
            <select
              className="text-input"
              value={selectedApk}
              onChange={(e) => { setSelectedApk(e.target.value); if (e.target.value) setApkUrl(''); }}
              disabled={isRunning || !!apkUrl}
            >
              <option value="">-- Select from Server --</option>
              {existingApks.map((name) => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </div>

          <div className="action-row mt-4">
            <button
              onClick={handleRunTest}
              disabled={isRunning}
              className={`run-button ${isRunning ? 'disabled' : ''}`}
            >
              <Play size={18} fill="currentColor" />
              {isDownloading ? 'Downloading...' : (isRunning ? 'Running Tests...' : 'Start Automation')}
            </button>

            {isRunning && (
              <button onClick={handleStopTest} className="run-button stop-button ml-2">
                Stop
              </button>
            )}

            {/* --- NEW: Reset / New Test Button --- */}
            {!isRunning && logs.length > 0 && (
              <button
                onClick={handleReset}
                className="run-button ml-2"
                style={{
                  backgroundColor: '#334155',
                  color: '#e2e8f0',
                  border: '1px solid #475569'
                }}
              >
                Start New Test
              </button>
            )}
          </div>
        </div>

        {/* Panel 2: Module Flow */}
        <div className="grid-item-flow">
          <ModuleFlow
            modules={modules}
            isRunning={isRunning}
            onToggleModule={toggleModuleSelection}
          />
        </div>

        {/* Panel 3: Live Metrics  */}
        {/* <div className="grid-item-chart">
          <MetricsChart data={metrics} />
        </div> */}

        {/* Panel 4: Logs */}
        <div className="grid-item-logs">
          <LogConsole logs={logs}
          statusMode={getConsoleStatus()} 
          />
        </div>
      </div>
    </div>
  );
}

export default App;