import React, { useState, useEffect, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import Header from "../Header/Header";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Play, Terminal, Activity, CheckCircle, Circle, AlertCircle, Cpu, Maximize2, Minimize2 } from 'lucide-react';
import UIScreenshotIssues from '../UIScreenshotIssues/UIScreenshotIssues';
import IssuePanel from '../IssuePanel/IssuePanel';
import NetworkConfigPanel from '../NetworkConfig/NetworkConfig'
import '../../App.css';

const WS_URL = 'ws://localhost:8000/ws/test-status';
const API_URL = 'http://localhost:8000';

const APP_VARIANTS = {
    FARMER: {
        id: "regular_farmer",
        label: "Krishivaas Farmer (Regular)",
        modules: [
            { name: 'Login', path: 'tests/test_cases/regular_farmer_test_cases/test_login_pytest.py' },
            { name: 'Onboarding', path: 'tests/test_cases/regular_farmer_test_cases/TestOnboarding.py' },
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

/* ─── ModuleFlow ─────────────────────────────────────────────────────────── */
const ModuleFlow = ({ modules, isRunning, onToggleModule }) => (
    <div className="dashboard-card">
        <h3 className="card-title">
            <Activity size={20} className="icon-blue" /> Module Flow Status
        </h3>
        <div className="module-list">
            {modules.map((mod, idx) => {
                let statusClass = "status-pending";
                let icon = <Circle size={16} />;
                if (mod.status === 'completed') { statusClass = "status-success"; icon = <CheckCircle size={16} />; }
                else if (mod.status === 'running') { statusClass = "status-running"; icon = <Activity size={16} className="icon-pulse" />; }
                else if (mod.status === 'failed') { statusClass = "status-failed"; icon = <AlertCircle size={16} />; }

                return (
                    <div key={idx}
                        className={`module-item ${statusClass} ${!isRunning ? "clickable-module" : ""}`}
                        onClick={() => !isRunning && onToggleModule(idx)}
                        style={{ cursor: !isRunning ? 'pointer' : 'default' }}>
                        {!isRunning ? (
                            <input type="checkbox" checked={!!mod.isSelected}
                                onClick={e => e.stopPropagation()}
                                onChange={() => onToggleModule(idx)}
                                className="mr-2 cursor-pointer" style={{ marginRight: '0px' }} />
                        ) : (
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

/* ─── MetricsChart ───────────────────────────────────────────────────────── */
const MetricsChart = ({ data }) => (
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
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#e2e8f0' }} itemStyle={{ color: '#e2e8f0' }} />
                    <Line yAxisId="left" type="monotone" dataKey="cpu" stroke="#38bdf8" strokeWidth={2} dot={false} animationDuration={300} />
                    <Line yAxisId="right" type="monotone" dataKey="memory" stroke="#c084fc" strokeWidth={2} dot={false} animationDuration={300} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    </div>
);

const staticApiLogs = [
    { time: "10:00:01.234", type: "info", message: "GET /api/v1/health-check - 200 OK (12ms)" },
    { time: "10:00:02.100", type: "info", message: "POST /api/v1/auth/login - 200 OK (45ms)" },
    { time: "10:00:05.400", type: "error", message: "GET /api/v1/users/profile - 401 Unauthorized (8ms)" },
    { time: "10:00:08.220", type: "warn", message: "Rate limit threshold approaching for IP 192.168.1.105" },
    { time: "10:00:15.000", type: "info", message: "GET /api/v1/dashboard/metrics - 200 OK (110ms)" },
];

/* ─── LogConsole ─────────────────────────────────────────────────────────── */
const LogConsole = ({ logs, statusMode = 'idle' }) => {
    const endRef = useRef(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [isFullScreen, setIsFullScreen] = useState(false);
    const [activeTab, setActiveTab] = useState('test');

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

    // Determine which logs to display based on the active tab
    const currentLogs = activeTab === 'test' ? logs : staticApiLogs;

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
          .log-tabs {
                    display: flex;
                    background-color: none;
                    border-bottom: 1px solid #334155;
                    padding: 0 16px;
                }
                .log-tab-btn {
                    background: none;
                    border: none;
                    color: #94a3b8;
                    padding: 8px 16px;
                    font-size: 0.85rem;
                    font-weight: 600;
                    cursor: pointer;
                    border-bottom: 2px solid transparent;
                    transition: all 0.2s;
                }
                .log-tab-btn:hover {
                    color: #e2e8f0;
                }
                .log-tab-btn.active {
                    color: #3b82f6;
                    border-bottom-color: #3b82f6;
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
                        placeholder={`Search ${activeTab} logs...`}
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
            {/* Tabs Row */}
            <div className="log-tabs">
                <button 
                    className={`log-tab-btn ${activeTab === 'test' ? 'active' : ''}`}
                    onClick={() => setActiveTab('test')}
                >
                    Test Logs
                </button>
                <button 
                    className={`log-tab-btn ${activeTab === 'api' ? 'active' : ''}`}
                    onClick={() => setActiveTab('api')}
                >
                    API Logs
                </button>
            </div>
            <div className="console-body">
                 {currentLogs.map((log, i) => {
                    const isMatch = matchesSearch(log);
                    return (
                        <div
                            key={i}
                            className={`log-line ${log.type.toLowerCase()} ${isMatch ? 'log-line-highlight' : ''}`}
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

/* ─── TestScreen ─────────────────────────────────────────────────────────── */
/**
 * Props:
 *   onHistoryUpdate(entry) — injected by App.jsx (JiraHistoryContext).
 *     Called by IssuePanel when user clicks Create → entry.type="created"
 *     Called by IssuePanel when user clicks Remove → entry.type="removed"
 *     JiraHistory screen reads these entries to populate Assigned/Unassigned tabs.
 */
function TestScreen({ onHistoryUpdate }) {

    const loadState = (key, fallback) => {
        try { const s = sessionStorage.getItem(key); return s ? JSON.parse(s) : fallback; }
        catch { return fallback; }
    };

    const [apkUrl, setApkUrl] = useState(() => loadState('apkUrl', ''));
    const [isRunning, setIsRunning] = useState(() => loadState('isRunning', false));
    const [isDownloading, setIsDownloading] = useState(false);
    const [showUiIssuesScreen, setShowUiIssuesScreen] = useState(false);
    const [uiAnalysisStatus, setUiAnalysisStatus] = useState('idle');
    const [uiAnalysisError, setUiAnalysisError] = useState('');
    const [uiAnalysisResults, setUiAnalysisResults] = useState([]);
    const [logs, setLogs] = useState(() => loadState('logs', []));
    const [metrics, setMetrics] = useState([]);
    const [appIcon, setAppIcon] = useState(null);
    const [appTitle, setAppTitle] = useState('');
    const [isDeviceConnected, setIsDeviceConnected] = useState(false);
    const [appiumStatus, setAppiumStatus] = useState('stopped');
    const [showStopPopup, setShowStopPopup] = useState(false);
    const [selectedAppKey, setSelectedAppKey] = useState(() => loadState('selectedAppKey', 'FARMER'));
    const [existingApks, setExistingApks] = useState([]);
    const [selectedApk, setSelectedApk] = useState(() => loadState('selectedApk', ''));
    const [hasOpenedReport, setHasOpenedReport] = useState(false);

    const prevAppKeyRef = useRef(selectedAppKey);

    const [modules, setModules] = useState(() => {
        const saved = sessionStorage.getItem('modules');
        if (saved) return JSON.parse(saved);
        const variant = APP_VARIANTS[selectedAppKey] || APP_VARIANTS['FARMER'];
        return variant.modules.map(m => ({ ...m, status: 'pending', isSelected: true }));
    });

    // Persist state
    useEffect(() => {
        sessionStorage.setItem('apkUrl', JSON.stringify(apkUrl));
        sessionStorage.setItem('isRunning', JSON.stringify(isRunning));
        sessionStorage.setItem('selectedAppKey', JSON.stringify(selectedAppKey));
        sessionStorage.setItem('modules', JSON.stringify(modules));
        sessionStorage.setItem('selectedApk', JSON.stringify(selectedApk));
        sessionStorage.setItem('logs', JSON.stringify(logs.slice(-200)));
    }, [apkUrl, isRunning, selectedAppKey, modules, selectedApk, logs]);

    const getConsoleStatus = () => {
        if (isRunning) return 'running';
        const active = modules.filter(m => m.isSelected);
        if (!active.length) return 'idle';
        if (active.some(m => m.status === 'failed')) return 'failure';
        const hasCompleted = active.some(m => m.status === 'completed' || m.status === 'passed');
        const hasRunning = active.some(m => m.status === 'running');
        if (hasCompleted && !hasRunning) return 'success';
        return 'idle';
    };

    useEffect(() => {
        if (prevAppKeyRef.current !== selectedAppKey) {
            setModules(APP_VARIANTS[selectedAppKey].modules.map(m => ({ ...m, status: 'pending', isSelected: true })));
            prevAppKeyRef.current = selectedAppKey;
        }
    }, [selectedAppKey]);

    const toggleModuleSelection = (index) => {
        if (isRunning) return;
        setModules(prev => prev.map((m, i) => i === index ? { ...m, isSelected: !m.isSelected } : m));
    };

    const { lastJsonMessage, sendMessage, readyState } = useWebSocket(WS_URL, {
        shouldReconnect: () => true,
        onMessage: (event) => {
            try { handleIncomingData(JSON.parse(event.data)); } catch { }
        }
    });

    const handleIncomingData = (data) => {
        // IssuePanel handles JIRA_PAYLOAD via its own WebSocket — skip here
        if (data.type === 'JIRA_PAYLOAD') return;

        if (data.type === 'LOG') {
            const { message = '', status } = data.payload || {};

            if (status === 'PROGRESS') {
                setLogs(prev => {
                    if (prev.length > 0 && prev[prev.length - 1].type === 'PROGRESS') {
                        const n = [...prev];
                        n[n.length - 1] = { time: new Date().toLocaleTimeString(), message, type: status };
                        return n;
                    }
                    return [...prev, { time: new Date().toLocaleTimeString(), message, type: status }];
                });
                return;
            }

            setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), message, type: status || 'INFO' }]);

            if (message && (
                message.includes("Allure HTML report generated") ||
                message.includes("Skipping report generation") ||
                message.includes("Test execution interrupted") ||
                message.includes("Test process terminated")
            )) setIsRunning(false);

        } else if (data.type === 'MODULE') {
            const { module, status, message } = data.payload || {};
            if (module && status) {
                setModules(prev => {
                    const updated = prev.map(m =>
                        m.name.toLowerCase() === module.toLowerCase() ? { ...m, status } : m
                    );
                    if (!updated.some(m => m.status === 'running') && !updated.some(m => m.status === 'pending' && m.isSelected)) {
                        setIsRunning(false);
                    }
                    return updated;
                });
                if (message) setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), message: `[${module}] ${message}`, type: status.toUpperCase() }]);
            }
        } else if (data.type === 'RUN_COMPLETE') {
            setIsRunning(false);
        }
    };

    const handleRunTest = async () => {
        if (appiumStatus !== 'running') { alert("Appium Server is not running. Start it first."); return; }
        if (!apkUrl && !selectedApk) { alert("Please enter a Google Drive URL or select an existing APK!"); return; }
        const testsToRun = modules.filter(m => m.isSelected).map(m => ({ name: m.name, path: m.path }));
        if (!testsToRun.length) { alert("Please select at least one module to run."); return; }

        setHasOpenedReport(false);
        setModules(prev => prev.map(m => ({ ...m, status: 'pending' })));
        setIsRunning(true);
        setIsDownloading(!!apkUrl);
        setLogs([]);

        handleIncomingData({ type: 'LOG', payload: { message: `Initializing ${APP_VARIANTS[selectedAppKey].label} test with ${testsToRun.length} modules...`, status: 'INFO' } });

        try {
            const payload = { tests_to_run: testsToRun, app_type: APP_VARIANTS[selectedAppKey].id };
            const endpoint = selectedApk ? '/test/start-test-existing' : '/test/start-test';
            const body = selectedApk ? { ...payload, apk_name: selectedApk } : { ...payload, url: apkUrl };

            const response = await fetch(`${API_URL}${endpoint}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
            });
            const data = await response.json();

            if (!response.ok) {
                const detail = data?.detail || 'Failed to start test';
                handleIncomingData({ type: 'LOG', payload: { message: `❌ Server error: ${detail}`, status: 'FAILED' } });
                throw new Error(detail);
            }

            if (data.app_icon) setAppIcon(data.app_icon);
            if (data.app_name) setAppTitle(data.app_name);
            handleIncomingData({ type: 'LOG', payload: { message: `Backend accepted job. APK Path: ${data.apk_path}`, status: 'SUCCESS' } });

        } catch (error) {
            console.error("Error starting test:", error);
            handleIncomingData({ type: 'LOG', payload: { message: `Error: ${error.message}`, status: 'FAILED' } });
            setIsRunning(false);
        } finally {
            setIsDownloading(false);
        }
    };

    const handleStopTest = async () => {
        try { await fetch(`${API_URL}/test/stop-test`, { method: 'POST' }); } catch { }
        setIsRunning(false); setIsDownloading(false);
        handleIncomingData({ type: 'LOG', payload: { message: 'Test stopped by user.', status: 'FAILED' } });
        setShowStopPopup(true);
    };

    const handleGenerateReport = async () => {
        setShowStopPopup(false);
        try { await fetch(`${API_URL}/test/generate-report`, { method: 'POST' }); } catch { }
        handleIncomingData({ type: 'LOG', payload: { message: 'Generating partial report...', status: 'INFO' } });
    };

    const handleReset = () => {
        setIsRunning(false); setApkUrl(''); setSelectedApk(''); setLogs([]);
        setModules(prev => prev.map(m => ({ ...m, status: 'pending' })));
        ['apkUrl', 'selectedApk', 'logs', 'modules', 'isRunning', 'jiraIssues'].forEach(k => sessionStorage.removeItem(k));
    };

    const analyzeUiScreenshots = async () => {
        setUiAnalysisStatus('loading'); setUiAnalysisError('');
        try {
            const res = await fetch(`${API_URL}/llm/ui-screenshots/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data?.detail || 'UI analysis failed');
            setUiAnalysisResults(data.results || []); setUiAnalysisStatus('ready');
        } catch (e) { setUiAnalysisStatus('error'); setUiAnalysisError(e?.message || 'Unknown error'); }
    };

    const checkAppiumStatus = async () => {
        try { const r = await fetch(`${API_URL}/test/appium/status`); setAppiumStatus((await r.json()).status); }
        catch { setAppiumStatus('stopped'); }
    };

    const toggleAppium = async () => {
        try {
            await fetch(`${API_URL}/test/appium/${appiumStatus === 'running' ? 'stop' : 'start'}`, { method: 'POST' });
            handleIncomingData({ type: 'LOG', payload: { message: `${appiumStatus === 'running' ? 'Stopping' : 'Starting'} Appium Server...`, status: 'INFO' } });
            setTimeout(checkAppiumStatus, 1000);
        } catch { }
    };

    useEffect(() => {
        const checkDevice = async () => {
            try { const r = await fetch(`${API_URL}/test/device-status`); setIsDeviceConnected(!!(await r.json()).connected); }
            catch { setIsDeviceConnected(false); }
        };
        const loadApks = async () => {
            try { const r = await fetch(`${API_URL}/test/apk-list`); setExistingApks((await r.json()).apks || []); } catch { }
        };
        loadApks(); checkDevice(); checkAppiumStatus();
        // Clear stale jiraIssues from old version (IssuePanel now manages its own)
        sessionStorage.removeItem('jiraIssues');
        const id = setInterval(() => { checkDevice(); checkAppiumStatus(); }, 5000);
        return () => clearInterval(id);
    }, []);

    /* ── Render ─────────────────────────────────────────────────────────────── */
    return (
        <div>
            <Header
                appIcon={appIcon} appTitle={appTitle}
                isDeviceConnected={isDeviceConnected} readyState={readyState}
                appiumStatus={appiumStatus}
                uiIssuesOpen={showUiIssuesScreen} uiIssuesLoading={uiAnalysisStatus === "loading"}
                onToggleUiIssues={() => setShowUiIssuesScreen(v => !v)}
            />

            {showUiIssuesScreen && (
                <div className="ui-issues-overlay" role="dialog" aria-modal="true">
                    <div className="ui-issues-overlay-inner">
                        <UIScreenshotIssues
                            status={uiAnalysisStatus} error={uiAnalysisError}
                            results={uiAnalysisResults} onAnalyzeClick={analyzeUiScreenshots}
                            onClose={() => setShowUiIssuesScreen(false)} />
                    </div>
                </div>
            )}

            {showStopPopup && (
                <div style={{ position: 'fixed', top: '30%', left: 0, right: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="dashboard-card" style={{ width: '400px', padding: '24px', border: '1px solid #ebebeb' }}>
                        <h3 style={{ marginTop: 0, color: '#333', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <AlertCircle color="#f59e0b" /> Test Stopped
                        </h3>
                        <p style={{ color: '#94a3b8', margin: '16px 0 24px 0' }}>
                            Tests were stopped manually. Generate the partial report?
                        </p>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                            <button onClick={() => setShowStopPopup(false)}
                                style={{ padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', backgroundColor: 'transparent', border: '1px solid #475569', color: '#333' }}>
                                No, Close
                            </button>
                            <button onClick={handleGenerateReport}
                                style={{ padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', backgroundColor: '#3b82f6', border: 'none', color: 'white', fontWeight: '500' }}>
                                Yes, Generate Report
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="dashboard-grid">
                <div className='dashboard-grid-1'>
                    <div className="dashboard-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '15px', marginBottom: '15px', borderBottom: '1px solid #334155' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: appiumStatus === 'running' ? '#4ade80' : '#ef4444', boxShadow: appiumStatus === 'running' ? '0 0 8px #4ade80' : 'none' }} />
                                <span className="input-label" style={{ marginBottom: 0 }}>Appium Server</span>
                            </div>
                            <button onClick={toggleAppium} className="input-label"
                                style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #CBD5E1', backgroundColor: appiumStatus === 'running' ? '#1e293b' : '#0f172a', color: appiumStatus === 'running' ? '#ef4444' : '#4ade80', cursor: 'pointer', fontWeight: '600', transition: 'all 0.2s' }}>
                                {appiumStatus === 'running' ? 'Stop Server' : 'Start Server'}
                            </button>
                        </div>
                        <div className="input-group mb-4">
                            <label className="input-label">Select Application</label>
                            <div className="select-wrapper">
                                <select className="text-input" value={selectedAppKey} onChange={e => setSelectedAppKey(e.target.value)} disabled={isRunning}>
                                    {Object.entries(APP_VARIANTS).map(([key, cfg]) => (
                                        <option key={key} value={key}>{cfg.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="input-group">
                            <label className="input-label">APK Source (Drive URL)</label>
                            <input type="text" placeholder="https://drive.google.com/..." value={apkUrl}
                                onChange={e => { setApkUrl(e.target.value); if (e.target.value) setSelectedApk(''); }}
                                className="text-input" disabled={isRunning || !!selectedApk} />
                        </div>

                        <div className="input-group mt-2">
                            <label className="input-label">OR Select Existing APK</label>
                            <select className="text-input" value={selectedApk}
                                onChange={e => { setSelectedApk(e.target.value); if (e.target.value) setApkUrl(''); }}
                                disabled={isRunning || !!apkUrl}>
                                <option value="">-- Select from Server --</option>
                                {existingApks.map(name => <option key={name} value={name}>{name}</option>)}
                            </select>
                        </div>

                        <div className="action-row mt-4">
                            <button onClick={handleRunTest} disabled={isRunning} className={`run-button ${isRunning ? 'disabled' : ''}`}>
                                <Play size={18} fill="currentColor" />
                                {isDownloading ? 'Downloading...' : isRunning ? 'Running Tests...' : 'Start Automation'}
                            </button>
                            {isRunning && (
                                <button onClick={handleStopTest} className="run-button stop-button ml-2">Stop</button>
                            )}
                            {!isRunning && logs.length > 0 && (
                                <button onClick={handleReset} className="run-button ml-2"
                                    style={{ backgroundColor: '#334155', color: '#e2e8f0', border: '1px solid #475569' }}>
                                    Start New Test
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Module Flow */}
                    <div className="grid-item-flo">
                        <ModuleFlow modules={modules} isRunning={isRunning} onToggleModule={toggleModuleSelection} />
                    </div>
                </div>
                <div>
                    <NetworkConfigPanel />
                </div>
                <div className="grid-item-chart">
                    <MetricsChart data={metrics} />
                </div>

                {/* Logs + IssuePanel */}
                <div className="grid-item-logs" style={{ display: 'flex', gap: '1rem', alignItems: 'stretch' }}>
                    <div style={{ flex: '0 0 60%', minWidth: 0 }}>
                        <LogConsole logs={logs} statusMode={getConsoleStatus()} />
                    </div>
                    <div style={{ flex: '0 0 calc(40% - 1rem)', minWidth: 0 }}>
                        <IssuePanel
                            modules={modules}
                            onHistoryUpdate={onHistoryUpdate}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default TestScreen;