import React, { useState, useEffect, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import Header from "../Header/Header";
// import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'; // disabled: MetricsChart
import { Play, Terminal, Activity, CheckCircle, Circle, AlertCircle, /* Cpu, */ Maximize2, Minimize2 } from 'lucide-react';
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
            { name: 'Crophealth', path: 'tests/test_cases/regular_farmer_test_cases/test_crop_health_pytest.py' },
            { name: 'Farmer Updates ', path: 'tests/test_cases/regular_farmer_test_cases/test_farmer_updates.py' },
            { name: 'Diagnosis Updates', path: 'tests/test_cases/regular_farmer_test_cases/test_diagnosis_updates.py' },
            { name: 'Onboarding', path: 'tests/test_cases/regular_farmer_test_cases/test_onboarding_pytest.py' },
        ]
    },
    CLIENT: {
        id: "regular_client",
        label: "Krishivaas Client (Regular)",
        modules: [
            { name: 'Login', path: 'tests/test_cases/regular_client_test_cases/login_pytest.py' },
            { name: 'Marketplace', path: 'tests/test_cases/regular_client_test_cases/test_marketplace.py' },
            { name: 'Cart', path: 'tests/test_cases/regular_client_test_cases/test_cart.py' },
        ]
    },
    STATE_FARMER: {
        id: "state_farmer",
        label: "State Farmer App",
        modules: [
            { name: 'Login', path: 'tests/test_cases/state_farmer_test_cases/test_login.py' },
            {name: 'Farmer Updates', path: 'tests/test_cases/state_farmer_test_cases/farmer_updates.py'},
            {name: 'Diagnosis Updates', path: 'tests/test_cases/state_farmer_test_cases/diagnosis_updates.py'},
        ]
    },
    STATE_CLIENT: {
        id: "state_client",
        label: "State Client App",
        modules: [
            { name: 'Login', path: 'tests/test_cases/state_client_test_cases/test_login.py' },
            { name: 'Tenders', path: 'tests/test_cases/state_client_test_cases/test_tenders.py' },
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
/* Temporarily disabled — live profiler metrics are not yet wired to a
   backend data source. Re-enable once the /ws/metrics endpoint is ready.
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
*/

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
    const [apiLogs, setApiLogs] = useState([]);

    const normalizedSearch = searchTerm.toLowerCase().trim();

    const matchesSearch = (log) => {
        if (!normalizedSearch) return false;
        return (
            log.message.toLowerCase().includes(normalizedSearch) ||
            log.type.toLowerCase().includes(normalizedSearch) ||
            String(log.time).toLowerCase().includes(normalizedSearch)
        );
    };

    /* Status bar — animated stripe while running, solid colour on result */
    const getBarStyle = () => {
        const base = { height: '3px', flexGrow: 1, margin: '0 12px', borderRadius: '2px', transition: 'all 0.3s ease' };
        if (statusMode === 'running')  return { ...base, background: 'linear-gradient(90deg,#bfdbfe 0%,#2563EB 50%,#bfdbfe 100%)', backgroundSize: '200% 100%', animation: 'gradientLoad 2s linear infinite' };
        if (statusMode === 'failure')  return { ...base, background: '#DC2626', animation: 'blinkRed 1.5s infinite' };
        if (statusMode === 'success')  return { ...base, background: '#059669', animation: 'blinkGreen 1.5s infinite' };
        return { ...base, background: '#E2E8F0' };
    };

    const currentLogs = activeTab === 'test' ? logs : apiLogs;

    /* Auto-scroll to bottom on new logs */
    useEffect(() => {
        if (endRef.current) endRef.current.scrollIntoView({ behavior: 'smooth' });
    }, [currentLogs.length]);

    useEffect(() => {
        if (activeTab !== 'api') return;
        const interval = setInterval(async () => {
            try {
                const res  = await fetch('http://localhost:8000/api-testing/logs');
                const data = await res.json();
                setApiLogs(data.map(log => ({
                    time:    log.timestamp,
                    type:    log.status >= 400 ? 'error' : 'info',
                    message: `${log.method} ${log.endpoint} - ${log.status} (${log.response_time_ms} ms)`,
                })).reverse());
            } catch { /* ignore */ }
        }, 2000);
        return () => clearInterval(interval);
    }, [activeTab]);

    return (
        <div className={`log-console ${isFullScreen ? 'full-screen' : ''}`}>

            {/* ── Header row ── */}
            <div className="console-header-row">
                <h3 className="console-header">
                    <Terminal size={13} /> LIVE LOGS
                </h3>
                <div style={getBarStyle()} />
                <div className="log-search">
                    <input
                        type="text"
                        placeholder={`Search logs…`}
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        className="text-input"
                        style={{ width: '160px', padding: '4px 8px', fontSize: '0.72rem' }}
                    />
                </div>
                <button
                    onClick={() => setIsFullScreen(f => !f)}
                    title={isFullScreen ? 'Exit Full Screen' : 'Full Screen'}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94A3B8', display: 'flex', alignItems: 'center', padding: '3px', marginLeft: '4px' }}
                >
                    {isFullScreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                </button>
            </div>

            {/* ── Tab row ── */}
            <div className="log-tabs">
                <button className={`log-tab-btn ${activeTab === 'test' ? 'active' : ''}`} onClick={() => setActiveTab('test')}>Test Logs</button>
                <button className={`log-tab-btn ${activeTab === 'api'  ? 'active' : ''}`} onClick={() => setActiveTab('api')}>API Logs</button>
            </div>

            {/* ── Log lines ── */}
            <div className="console-body">
                {currentLogs.length === 0 && (
                    <div style={{ color: '#94A3B8', fontSize: '0.75rem', padding: '1.5rem', textAlign: 'center' }}>
                        No logs yet — start a test run to see output here.
                    </div>
                )}
                {currentLogs.map((log, i) => (
                    <div key={i} className={`log-line ${log.type.toLowerCase()} ${matchesSearch(log) ? 'log-line-highlight' : ''}`}>
                        <span className="timestamp">[{log.time}]</span>
                        <span className="message">{log.message}</span>
                    </div>
                ))}
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
    const [networkConfig, setNetworkConfig] = useState(null);
    const [showNewTestButton, setShowNewTestButton] = useState(false);


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
            setShowNewTestButton(true);
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
        setShowNewTestButton(false);
        setIsDownloading(!!apkUrl);
        setLogs([]);

        handleIncomingData({ type: 'LOG', payload: { message: `Initializing ${APP_VARIANTS[selectedAppKey].label} test with ${testsToRun.length} modules...`, status: 'INFO' } });

        try {
            const runId = crypto.randomUUID();

            // Save network config against this run_id BEFORE starting tests
            // if (networkConfig?.enabled) {
            //     try {
            //         await fetch(`${API_URL}/network-simulate/apply`, {
            //             method: 'POST',
            //             headers: { 'Content-Type': 'application/json' },
            //             body: JSON.stringify({ ...networkConfig, run_id: runId }),
            //         });

            //         // ✅ Log confirmation to the console
            //         handleIncomingData({
            //             type: 'LOG',
            //             payload: {
            //                 message: `📡 Network Simulation Applied → ${networkConfig.networkType} | ${networkConfig.download}Mbps ↓ | ${networkConfig.upload}Mbps ↑ | ${networkConfig.latency}ms latency | ${networkConfig.packetLoss}% loss`,
            //                 status: 'INFO'
            //             }
            //         });

            //     } catch (err) {
            //         console.warn("Network config apply failed:", err);
            //         handleIncomingData({
            //             type: 'LOG',
            //             payload: { message: `⚠️ Network config apply failed: ${err.message}`, status: 'FAILED' }
            //         });
            //     }
            // }

            const payload = { tests_to_run: testsToRun, app_type: APP_VARIANTS[selectedAppKey].id, run_id: runId };
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
        try { 
            await fetch(`${API_URL}/test/stop-test`, { 
                method: 'POST' 
            });
         } catch { }

        setIsRunning(false); 
        setIsDownloading(false);
        setShowNewTestButton(true);
        handleIncomingData({ type: 'LOG', payload: { message: 'Test stopped by user.', status: 'FAILED' } });
        setShowStopPopup(true);
    };

    const handleGenerateReport = async () => {
        setShowStopPopup(false);
        try { await fetch(`${API_URL}/test/generate-report`, { method: 'POST' }); } catch { }
        handleIncomingData({ type: 'LOG', payload: { message: 'Generating partial report...', status: 'INFO' } });
    };
    const handleReset = async () => {

        setShowNewTestButton(false);

        // Clear UI states
        setIsRunning(false);
        setIsDownloading(false);

        // Clear APK selections
        setApkUrl('');
        setSelectedApk('');

        // Clear app details
        setAppIcon(null);
        setAppTitle('');

        // Clear logs completely
        setLogs([]);

        // Reset module statuses
        setModules(
            APP_VARIANTS[selectedAppKey].modules.map(m => ({
                ...m,
                status: 'pending',
                isSelected: true
            }))
        );

        // Clear session storage
        [
            'apkUrl',
            'selectedApk',
            'logs',
            'modules',
            'isRunning',
            'jiraIssues'
        ].forEach(k => sessionStorage.removeItem(k));

        // Re-fetch fresh statuses
        await checkAppiumStatus();

        handleIncomingData({
            type: 'LOG',
            payload: {
                message: 'Ready for new test execution.',
                status: 'INFO'
            }
        });
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
            setLogs(prev => [
                ...prev,
                {
                    time: new Date().toLocaleTimeString(),
                    message: `Appium server ${appiumStatus === 'running' ? 'stopping' : 'starting'}...`,
                    type: 'SYSTEM'
                }
            ]);
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
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="dashboard-card" style={{ width: '400px', padding: '24px', boxShadow: '0 20px 48px rgba(15,23,42,0.18)' }}>
                        <h3 style={{ margin: '0 0 8px', color: '#0F172A', fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <AlertCircle size={18} color="#D97706" /> Test Stopped
                        </h3>
                        <p style={{ color: '#64748B', margin: '0 0 20px', fontSize: '0.85rem', lineHeight: '1.6' }}>
                            Tests were stopped manually. Would you like to generate a partial Allure report from the results collected so far?
                        </p>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                            <button onClick={() => setShowStopPopup(false)}
                                style={{ padding: '7px 16px', borderRadius: '6px', cursor: 'pointer', background: 'transparent', border: '1px solid #E2E8F0', color: '#475569', fontSize: '0.8rem', fontWeight: 600, fontFamily: 'inherit' }}>
                                No, Close
                            </button>
                            <button onClick={handleGenerateReport}
                                style={{ padding: '7px 18px', borderRadius: '6px', cursor: 'pointer', background: '#2563EB', border: 'none', color: '#fff', fontSize: '0.8rem', fontWeight: 600, fontFamily: 'inherit' }}>
                                Yes, Generate Report
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Two-panel layout: left = controls, right = logs+issues ── */}
            <div className="dashboard-grid">

                {/* ── LEFT PANEL: Appium controls + Module Flow + Network Config ── */}
                <div className="dashboard-left-panel">

                    {/* Controls card */}
                    <div className="dashboard-card">
                        {/* Appium server row */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '12px', marginBottom: '12px', borderBottom: '1px solid #E2E8F0' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                                <div style={{ width: '9px', height: '9px', borderRadius: '50%', backgroundColor: appiumStatus === 'running' ? '#059669' : '#DC2626', boxShadow: appiumStatus === 'running' ? '0 0 0 3px rgba(5,150,105,.15)' : 'none', flexShrink: 0 }} />
                                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#475569', letterSpacing: '0.03em' }}>APPIUM SERVER</span>
                                <span style={{ fontSize: '0.68rem', fontWeight: 600, color: appiumStatus === 'running' ? '#059669' : '#94A3B8', background: appiumStatus === 'running' ? '#ECFDF5' : '#F1F5F9', borderRadius: '4px', padding: '1px 6px' }}>
                                    {appiumStatus === 'running' ? 'Running' : 'Stopped'}
                                </span>
                            </div>
                            <button
                                onClick={toggleAppium}
                                style={{ padding: '5px 12px', borderRadius: '6px', border: appiumStatus === 'running' ? '1px solid #FECACA' : '1px solid #BFDBFE', backgroundColor: appiumStatus === 'running' ? '#FEF2F2' : '#EFF6FF', color: appiumStatus === 'running' ? '#DC2626' : '#2563EB', cursor: 'pointer', fontWeight: 700, fontSize: '0.72rem', fontFamily: 'inherit', transition: 'all 0.15s' }}>
                                {appiumStatus === 'running' ? 'Stop' : 'Start'}
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
                            {showNewTestButton && (
                                <button onClick={handleReset} className="run-button ml-2"
                                    style={{ backgroundColor: '#F1F5F9', color: '#475569', border: '1px solid #E2E8F0', boxShadow: 'none' }}>
                                    Start New Test
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Module Flow status */}
                    <div className="grid-item-flo">
                        <ModuleFlow modules={modules} isRunning={isRunning} onToggleModule={toggleModuleSelection} />
                    </div>

                    {/* Network Config */}
                    <NetworkConfigPanel setNetworkConfig={setNetworkConfig} />

                </div>{/* /dashboard-left-panel */}

                {/* ── RIGHT PANEL: Live Logs + Issue Panel side by side ── */}
                <div className="dashboard-right-panel">
                    {/* Log console — grows to fill all remaining width */}
                    <div style={{ flex: '1 1 auto', minWidth: 0, overflow: 'hidden' }}>
                        <LogConsole logs={logs} statusMode={getConsoleStatus()} />
                    </div>
                    {/* Issue panel — fixed 340px, never overflows */}
                    <div style={{ flex: '0 0 340px', width: '340px', display: 'flex', flexDirection: 'column' }}>
                        <IssuePanel
                            modules={modules}
                            onHistoryUpdate={onHistoryUpdate}
                        />
                    </div>
                </div>{/* /dashboard-right-panel */}

            </div>{/* /dashboard-grid */}
        </div>
    );
}

export default TestScreen;