import React, { useState, useEffect, useRef } from 'react';
import './APIMatrixTester.css';
import { Play, SquareX, Download, Plus, X, Copy, AlertCircle } from 'lucide-react';

const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/test-status';

const COLOR_MAP = {
  cyan: { text: '#4fc3f7', bg: 'rgba(79,195,247,.1)', border: 'rgba(79,195,247,.3)' },
  green: { text: '#4ade80', bg: 'rgba(74,222,128,.1)', border: 'rgba(74,222,128,.3)' },
  amber: { text: '#fbbf24', bg: 'rgba(251,191,36,.1)', border: 'rgba(251,191,36,.3)' },
  red: { text: '#f87171', bg: 'rgba(248,113,113,.1)', border: 'rgba(248,113,113,.3)' },
  purple: { text: '#c084fc', bg: 'rgba(192,132,252,.1)', border: 'rgba(192,132,252,.3)' },
  blue: { text: '#60a5fa', bg: 'rgba(96,165,250,.1)', border: 'rgba(96,165,250,.3)' },
};

const uid = () => Math.random().toString(36).slice(2, 9);

const ts = () => {
  const n = new Date();
  return `${String(n.getHours()).padStart(2, '0')}:${String(n.getMinutes()).padStart(2, '0')}:${String(n.getSeconds()).padStart(2, '0')}.${String(n.getMilliseconds()).padStart(3, '0')}`;
};

const fetchWithTimeout = async (url, options, timeout = 10000) => {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), timeout);
  try {
    const r = await fetch(url, { ...options, signal: ctrl.signal });
    clearTimeout(id);
    return r;
  } catch (e) {
    clearTimeout(id);
    throw e;
  }
};

export default function APIMatrixTester() {
  const [endpoints, setEndpoints] = useState([
    { id: 'ep-1', method: 'GET', name: 'List Users', path: '/users', auth: 'none', body: '', expectedCodes: [200], envIds: ['env-dev', 'env-staging', 'env-prod'] },
    { id: 'ep-2', method: 'GET', name: 'Get Post', path: '/posts/1', auth: 'none', body: '', expectedCodes: [200], envIds: ['env-dev', 'env-staging', 'env-prod'] },
    { id: 'ep-3', method: 'POST', name: 'Create Post', path: '/posts', auth: 'none', body: '{"title":"test","body":"hello","userId":1}', expectedCodes: [201], envIds: ['env-dev', 'env-staging'] },
    { id: 'ep-4', method: 'GET', name: 'Get Todos', path: '/todos?_limit=5', auth: 'none', body: '', expectedCodes: [200], envIds: ['env-dev', 'env-staging', 'env-prod'] },
    { id: 'ep-5', method: 'PUT', name: 'Update User', path: '/users/1', auth: 'none', body: '{"name":"Updated"}', expectedCodes: [200], envIds: ['env-dev'] },
    { id: 'ep-6', method: 'DELETE', name: 'Delete Post', path: '/posts/1', auth: 'none', body: '', expectedCodes: [200], envIds: ['env-dev', 'env-staging'] },
  ]);

  const [environments, setEnvironments] = useState([
    { id: 'env-dev', name: 'development', baseUrl: 'https://jsonplaceholder.typicode.com', color: 'cyan', token: '', headers: {} },
    { id: 'env-staging', name: 'staging', baseUrl: 'https://jsonplaceholder.typicode.com', color: 'amber', token: '', headers: {} },
    { id: 'env-prod', name: 'production', baseUrl: 'https://jsonplaceholder.typicode.com', color: 'green', token: '', headers: {} },
  ]);

  const [results, setResults] = useState({});
  const [logs, setLogs] = useState([]);
  const [currentView, setCurrentView] = useState('matrix');
  const [running, setRunning] = useState(false);
  const [stopFlag, setStopFlag] = useState(false);
  const [selectedCell, setSelectedCell] = useState(null);
  const [groupBy, setGroupBy] = useState('env');
  const [activeFilters, setActiveFilters] = useState({ pass: true, fail: true, pending: true, skip: true });
  const [activeResult, setActiveResult] = useState(null);
  const [resultPane, setResultPane] = useState('response');
  const logEndRef = useRef(null);

  // Modals
  const [showEndpointModal, setShowEndpointModal] = useState(false);
  const [showEnvModal, setShowEnvModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingModal, setEditingModal] = useState({
    method: 'GET',
    name: '',
    path: '',
    auth: 'none',
    body: '',
    expectedCodes: '200',
    envIds: [],
  });
  const [editingEnvModal, setEditingEnvModal] = useState({
    name: '',
    baseUrl: '',
    color: 'cyan',
    token: '',
    headers: '',
  });
  const [importText, setImportText] = useState('');
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [lastRunTime, setLastRunTime] = useState(null);

  const appendLog = (level, msg, cls = '') => {
    setLogs(prev => [{ level, msg, cls, time: ts() }, ...prev.slice(0, 199)]);
  };

  // Load data from backend on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [endpointsRes, environmentsRes] = await Promise.all([
          fetch(`${API_URL}/api/matrix/endpoints`),
          fetch(`${API_URL}/api/matrix/environments`),
        ]);

        if (endpointsRes.ok) {
          const eps = await endpointsRes.json();
          if (eps.length > 0) setEndpoints(eps);
        }

        if (environmentsRes.ok) {
          const envs = await environmentsRes.json();
          if (envs.length > 0) setEnvironments(envs);
        }

        appendLog('INFO', 'Connected to backend API', 'll-info');
      } catch (e) {
        appendLog('WARN', `Could not load from backend: ${e.message}`, 'll-warn');
      }
    };

    loadData();

    // Setup WebSocket for live updates
    try {
      const ws = new WebSocket(WS_URL);
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === 'API_MATRIX') {
          const payload = msg.payload;
          if (payload.action === 'test_result') {
            const result = payload.result;
            setResults(prev => ({ ...prev, [result.key]: result }));
          } else if (payload.action === 'batch_progress') {
            const result = payload.result;
            setResults(prev => ({ ...prev, [result.key]: result }));
          }
        }
      };
      ws.onerror = () => appendLog('WARN', 'WebSocket connection failed', 'll-warn');
    } catch (e) {
      appendLog('WARN', 'Could not connect to WebSocket', 'll-warn');
    }
  }, []);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollTop = 0;
    }
  }, [logs]);

  const runRequest = async (ep, env) => {
    const url = env.baseUrl.replace(/\/$/, '') + ep.path;
    const headers = { 'Content-Type': 'application/json', ...(env.headers || {}) };
    if (ep.auth === 'bearer' && env.token) headers['Authorization'] = env.token.startsWith('Bearer') ? env.token : 'Bearer ' + env.token;
    if (ep.auth === 'apikey' && env.token) headers['X-API-Key'] = env.token;

    const options = { method: ep.method, headers };
    if (['POST', 'PUT', 'PATCH'].includes(ep.method) && ep.body) {
      try {
        options.body = typeof ep.body === 'string' ? ep.body : JSON.stringify(ep.body);
      } catch (e) {}
    }

    const start = performance.now();
    let status = 0, body = null, error = null;
    try {
      const resp = await fetchWithTimeout(url, options, 8000);
      status = resp.status;
      const text = await resp.text();
      try {
        body = JSON.parse(text);
      } catch (e) {
        body = text;
      }
    } catch (e) {
      error = e.name === 'AbortError' ? 'Timeout after 8s' : e.message;
    }
    const duration = Math.round(performance.now() - start);

    const pass = !error && ep.expectedCodes.includes(status);
    return { url, status, body, error, duration, pass, envName: env.name, epName: ep.name, method: ep.method, timestamp: new Date().toISOString() };
  };

  const runSingleCell = async (epId, envId) => {
    const ep = endpoints.find(e => e.id === epId);
    const env = environments.find(e => e.id === envId);
    if (!ep || !env) return;

    const key = `${epId}::${envId}`;
    setResults(prev => ({ ...prev, [key]: { running: true } }));

    appendLog('RUN', `${ep.method} ${ep.path} [${env.name}]`, 'll-run');

    const res = await runRequest(ep, env);
    setResults(prev => ({ ...prev, [key]: res }));

    const logMsg = res.error ? `${ep.path} [${env.name}] — ${res.error}` : `${ep.path} [${env.name}] — ${res.status} (${res.duration}ms)`;
    appendLog(res.pass ? 'PASS' : 'FAIL', logMsg, res.pass ? 'll-pass' : 'll-fail');

    setActiveResult(res);
  };

  const runAllTests = async () => {
    if (running) return;
    setRunning(true);
    setStopFlag(false);
    setResults({});

    appendLog('INFO', `Starting matrix run — ${endpoints.length} endpoints × ${environments.length} environments`, 'll-info');

    try {
      const response = await fetch(`${API_URL}/api/matrix/run-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.ok) {
        const data = await response.json();
        const { results: testResults, summary } = data;

        // Update UI with all results
        const resultMap = {};
        testResults.forEach(r => {
          resultMap[r.key] = {
            pass_: r.pass_,
            status: r.status,
            duration: r.duration,
            error: r.error,
            envName: r.envName,
            epName: r.epName,
            method: r.method,
            body: r.body,
          };
        });
        setResults(resultMap);
        setLastRunTime(new Date().toLocaleString());

        appendLog('INFO', `Matrix run complete — ${summary.passed} passed, ${summary.failed} failed in ${summary.duration}ms`, 'll-info');
      } else {
        const error = await response.text();
        appendLog('FAIL', `Test execution failed: ${error}`, 'll-fail');
      }
    } catch (e) {
      appendLog('FAIL', `Error running tests: ${e.message}`, 'll-fail');
    }

    setRunning(false);
  };

  const saveEndpoint = async () => {
    const envIds = editingModal.envIds.length > 0 ? editingModal.envIds : environments.map(e => e.id);
    const expectedCodes = editingModal.expectedCodes.split(',').map(s => parseInt(s.trim())).filter(Boolean) || [200];

    const newEndpoint = {
      id: 'ep-' + uid(),
      method: editingModal.method,
      name: editingModal.name || editingModal.path,
      path: editingModal.path,
      auth: editingModal.auth,
      body: editingModal.body,
      expectedCodes,
      envIds,
    };

    // Save to backend
    try {
      const res = await fetch(`${API_URL}/api/matrix/endpoints`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newEndpoint),
      });

      if (res.ok) {
        setEndpoints(prev => [...prev, newEndpoint]);
        setShowEndpointModal(false);
        setEditingModal({ method: 'GET', name: '', path: '', auth: 'none', body: '', expectedCodes: '200', envIds: [] });
        appendLog('INFO', `Endpoint saved: ${newEndpoint.method} ${newEndpoint.path}`, 'll-info');
      } else {
        appendLog('FAIL', 'Failed to save endpoint to backend', 'll-fail');
      }
    } catch (e) {
      appendLog('FAIL', `Error saving endpoint: ${e.message}`, 'll-fail');
    }
  };

  const saveEnvironment = async () => {
    let headers = {};
    try {
      headers = JSON.parse(editingEnvModal.headers || '{}');
    } catch (e) {}

    const newEnvironment = {
      id: 'env-' + uid(),
      name: editingEnvModal.name,
      baseUrl: editingEnvModal.baseUrl,
      color: editingEnvModal.color,
      token: editingEnvModal.token,
      headers,
    };

    // Save to backend
    try {
      const res = await fetch(`${API_URL}/api/matrix/environments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newEnvironment),
      });

      if (res.ok) {
        setEnvironments(prev => [...prev, newEnvironment]);
        setShowEnvModal(false);
        setEditingEnvModal({ name: '', baseUrl: '', color: 'cyan', token: '', headers: '' });
        appendLog('INFO', `Environment added: ${newEnvironment.name}`, 'll-info');
      } else {
        appendLog('FAIL', 'Failed to save environment to backend', 'll-fail');
      }
    } catch (e) {
      appendLog('FAIL', `Error saving environment: ${e.message}`, 'll-fail');
    }
  };

  const doImport = async () => {
    try {
      const data = JSON.parse(importText);
      const arr = Array.isArray(data) ? data : [data];
      
      const newEndpoints = arr.map(item => ({
        id: 'ep-' + uid(),
        method: item.method || 'GET',
        name: item.name || item.path || '/',
        path: item.path || '/',
        auth: item.auth || 'none',
        body: item.body || '',
        expectedCodes: item.expectedCodes || [200],
        envIds: environments.map(e => e.id),
      }));

      // Save each imported endpoint to backend
      let saved = 0;
      for (const ep of newEndpoints) {
        try {
          const res = await fetch(`${API_URL}/api/matrix/endpoints`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(ep),
          });
          if (res.ok) saved++;
        } catch (e) {
          console.error('Error saving imported endpoint:', e);
        }
      }

      setEndpoints(prev => [...prev, ...newEndpoints]);
      setShowImportModal(false);
      setImportText('');
      appendLog('INFO', `Imported ${saved}/${arr.length} endpoints`, 'll-info');
    } catch (e) {
      appendLog('FAIL', 'Import failed: invalid JSON', 'll-fail');
    }
  };

  const exportResults = () => {
    const out = {
      exportedAt: new Date().toISOString(),
      environments: environments.map(e => ({ name: e.name, baseUrl: e.baseUrl })),
      endpoints: endpoints.map(e => ({ method: e.method, path: e.path, name: e.name })),
      results: Object.entries(results).map(([k, r]) => ({
        key: k,
        pass: r.pass,
        status: r.status,
        duration: r.duration,
        error: r.error,
      })),
      summary: {
        total: Object.keys(results).length,
        pass: Object.values(results).filter(r => r.pass).length,
        fail: Object.values(results).filter(r => !r.pass && !r.running).length,
      },
    };
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'api-matrix-results.json';
    a.click();
  };

  // Summary calculations
  const vals = Object.values(results).filter(r => !r.running);
  const summaryPass = vals.filter(r => r.pass).length;
  const summaryFail = vals.filter(r => !r.pass && !r.error).length;
  const total2 = endpoints.reduce((a, ep) => a + ep.envIds.length, 0);
  const summaryPending = Math.max(0, total2 - vals.length);

  // Matrix rendering
  let columns = [];
  if (groupBy === 'env') {
    columns = environments.map(e => ({ id: e.id, label: e.name, color: e.color }));
  } else if (groupBy === 'method') {
    const methods = [...new Set(endpoints.map(e => e.method))];
    columns = methods.map(m => ({
      id: m,
      label: m,
      color: { GET: 'blue', POST: 'green', PUT: 'amber', DELETE: 'red', PATCH: 'purple' }[m] || 'cyan',
    }));
  } else if (groupBy === 'auth') {
    const auths = [...new Set(endpoints.map(e => e.auth))];
    columns = auths.map(a => ({ id: a, label: a || 'none', color: 'cyan' }));
  }

  const MatrixCell = ({ endpoint, col }) => {
    let cellKey, applicable = false;
    if (groupBy === 'env') {
      cellKey = `${endpoint.id}::${col.id}`;
      applicable = endpoint.envIds.includes(col.id);
    } else if (groupBy === 'method') {
      cellKey = `${endpoint.id}::${col.id}`;
      applicable = endpoint.method === col.id;
      if (applicable) cellKey = `${endpoint.id}::${environments[0]?.id || 'default'}`;
    } else {
      cellKey = `${endpoint.id}::${environments[0]?.id || 'default'}`;
      applicable = endpoint.auth === col.id;
    }

    const res = results[cellKey];
    let cellClass = 'empty',
      statusTxt = '—',
      timeTxt = '',
      codeTxt = '';

    if (!applicable) {
      cellClass = 'empty';
      statusTxt = '—';
    } else if (!res) {
      cellClass = 'pending';
      statusTxt = 'PENDING';
      timeTxt = 'not run';
    } else if (res.running) {
      cellClass = 'running';
      statusTxt = '…';
      timeTxt = 'running';
    } else if (res.pass) {
      cellClass = 'pass';
      statusTxt = 'PASS';
      timeTxt = res.duration + 'ms';
      codeTxt = res.status;
    } else {
      cellClass = 'fail';
      statusTxt = 'FAIL';
      timeTxt = res.duration ? res.duration + 'ms' : 'error';
      codeTxt = res.status || 'ERR';
    }

    const passColor = cellClass.includes('pass')
      ? '#4ade80'
      : cellClass.includes('fail')
        ? '#f87171'
        : cellClass.includes('running')
          ? '#4fc3f7'
          : cellClass.includes('pending')
            ? '#fbbf24'
            : '#4a6070';

    return (
      <td
        className={`matrix-cell ${cellClass}`}
        onClick={() => {
          if (applicable && res) {
            setActiveResult(res);
          } else if (applicable && !res) {
            if (groupBy === 'env') {
              runSingleCell(endpoint.id, col.id);
            }
          }
        }}
      >
        <div className="cell-status" style={{ color: passColor }}>
          {statusTxt}
        </div>
        <div className="cell-code">{codeTxt}</div>
        <div className="cell-time">{timeTxt}</div>
      </td>
    );
  };

  const syntaxHighlight = json => {
    if (!json) return '';
    return json
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        match => {
          let cls = 'json-num';
          if (/^"/.test(match)) cls = /:$/.test(match) ? 'json-key' : 'json-str';
          else if (/true|false/.test(match)) cls = 'json-bool';
          else if (/null/.test(match)) cls = 'json-null';
          return `<span class="${cls}">${match}</span>`;
        }
      );
  };

  const LogEntry = ({ entry }) => (
    <div className="log-row">
      <span className="log-t">{entry.time}</span>
      <span className={`log-lvl ll-${entry.level.toLowerCase()}`}>{entry.level}</span>
      <span className="log-msg">{entry.msg}</span>
    </div>
  );

  const Modal = ({ title, open, onClose, children }) => (
    <div className={`overlay ${open ? 'open' : ''}`} onClick={e => e.target.classList.contains('overlay') && onClose()}>
      <div className="modal">
        <h3>{title}</h3>
        {children}
      </div>
    </div>
  );

  return (
    <div className="api-matrix-container">
      {/* TOPBAR */}
      <div className="topbar">
        <div className="logo">
          <div className="logo-mark">M</div>
          API <span>Matrix</span>
        </div>
        <div className="tab-bar">
          <button className={`tab ${currentView === 'matrix' ? 'active' : ''}`} onClick={() => setCurrentView('matrix')}>
            Matrix View
          </button>
          <button className={`tab ${currentView === 'builder' ? 'active' : ''}`} onClick={() => setCurrentView('builder')}>
            Request Builder
          </button>
        </div>
        <div className="topbar-right">
          <button className="btn" onClick={() => setShowImportModal(true)}>
            ⊕ Import
          </button>
          <button className="btn" onClick={() => setShowEndpointModal(true)}>
            + Endpoint
          </button>
          <div className="divider-v"></div>
          {!running ? (
            <button className="btn btn-cyan" onClick={runAllTests}>
              <Play size={14} /> Run All
            </button>
          ) : (
            <button className="btn btn-red" onClick={() => setStopFlag(true)}>
              <SquareX size={14} /> Stop
            </button>
          )}
          <button className="btn" onClick={exportResults}>
            <Download size={14} /> Export
          </button>
        </div>
      </div>

      {/* BODY */}
      <div className="body">
        {/* SIDEBAR */}
        <div className="sidebar">
          <div className="sidebar-header">
            Endpoints <span className="badge badge-pending">{endpoints.length}</span>
          </div>
          <div className="sidebar-body">
            <div className="sidebar-section">Endpoints</div>
            {endpoints.map(ep => {
              const mcls = { GET: 'get-m', POST: 'post-m', PUT: 'put-m', DELETE: 'del-m', PATCH: 'patch-m' }[ep.method] || 'get-m';
              return (
                <div key={ep.id} className="sidebar-item">
                  <span className={`item-method ${mcls}`}>{ep.method}</span>
                  <span className="item-path">{ep.path}</span>
                </div>
              );
            })}
          </div>

          <div style={{ borderTop: '1px solid var(--border)', padding: '10px 14px', marginTop: '-2px' }}>
            <div style={{ fontSize: '10px', color: 'var(--text3)', fontWeight: '600', letterSpacing: '.07em', textTransform: 'uppercase', marginBottom: '8px' }}>
              Environments
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {environments.map(env => {
                const c = COLOR_MAP[env.color] || COLOR_MAP.cyan;
                return (
                  <div key={env.id} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '5px 8px', background: c.bg, border: `1px solid ${c.border}`, borderRadius: '4px', fontSize: '11px' }}>
                    <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: c.text, flexShrink: 0 }}></span>
                    <span style={{ color: c.text, fontWeight: '600', minWidth: '70px' }}>{env.name}</span>
                    <span style={{ color: 'var(--text3)', fontFamily: 'JetBrains Mono, monospace', fontSize: '9px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100px' }} title={env.baseUrl}>
                      {env.baseUrl.replace('https://', '')}
                    </span>
                  </div>
                );
              })}
            </div>
            <button className="btn" style={{ marginTop: '8px', width: '100%', justifyContent: 'center', fontSize: '11px' }} onClick={() => setShowEnvModal(true)}>
              + Add Environment
            </button>
          </div>

          {/* SUMMARY SECTION */}
          <div style={{ borderTop: '1px solid var(--border)', padding: '10px 14px', marginTop: '0' }}>
            <button
              onClick={() => setShowSummaryModal(true)}
              style={{
                width: '100%',
                background: 'var(--bg2)',
                border: '1px solid var(--border)',
                color: 'var(--text2)',
                fontSize: '11px',
                fontWeight: '600',
                cursor: 'pointer',
                padding: '8px 10px',
                borderRadius: '4px',
                transition: 'all 0.15s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                marginBottom: '8px'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'var(--bg3)';
                e.target.style.color = 'var(--cyan)';
                e.target.style.borderColor = 'var(--cyan)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'var(--bg2)';
                e.target.style.color = 'var(--text2)';
                e.target.style.borderColor = 'var(--border)';
              }}
            >
              📊 Summary
            </button>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', fontSize: '10px' }}>
              <div style={{ padding: '6px 8px', background: 'rgba(22, 163, 74, 0.1)', border: '1px solid rgba(22, 163, 74, 0.3)', borderRadius: '3px', textAlign: 'center' }}>
                <div style={{ color: 'var(--text3)', fontSize: '9px', marginBottom: '2px' }}>Pass</div>
                <div style={{ color: 'var(--green)', fontWeight: '700', fontFamily: 'JetBrains Mono, monospace' }}>{summaryPass}</div>
              </div>
              <div style={{ padding: '6px 8px', background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.3)', borderRadius: '3px', textAlign: 'center' }}>
                <div style={{ color: 'var(--text3)', fontSize: '9px', marginBottom: '2px' }}>Fail</div>
                <div style={{ color: 'var(--red)', fontWeight: '700', fontFamily: 'JetBrains Mono, monospace' }}>{summaryFail}</div>
              </div>
              <div style={{ padding: '6px 8px', background: 'rgba(217, 119, 6, 0.1)', border: '1px solid rgba(217, 119, 6, 0.3)', borderRadius: '3px', textAlign: 'center' }}>
                <div style={{ color: 'var(--text3)', fontSize: '9px', marginBottom: '2px' }}>Pending</div>
                <div style={{ color: 'var(--amber)', fontWeight: '700', fontFamily: 'JetBrains Mono, monospace' }}>{summaryPending}</div>
              </div>
            </div>
          </div>
        </div>

        {/* MAIN */}
        <div className="main">
          {/* MATRIX VIEW */}
          {currentView === 'matrix' && (
            <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <div className="matrix-toolbar">
                <span className="matrix-toolbar-title">Matrix</span>
                <div className="filter-group">
                  <span className="filter-label">Group by:</span>
                  <select className="select" value={groupBy} onChange={e => setGroupBy(e.target.value)}>
                    <option value="env">Environment</option>
                    <option value="method">HTTP Method</option>
                    <option value="auth">Auth Type</option>
                  </select>
                </div>
                <div className="filter-group">
                  <span className="filter-label">Filter:</span>
                  {['pass', 'fail', 'pending', 'skip'].map(f => (
                    <div
                      key={f}
                      className={`pill ${activeFilters[f] ? 'on' : ''}`}
                      onClick={() => setActiveFilters(prev => ({ ...prev, [f]: !prev[f] }))}
                    >
                      {f.toUpperCase()}
                    </div>
                  ))}
                </div>
                <div style={{ marginLeft: 'auto', display: 'flex', gap: '6px' }}>
                  <button className="btn" onClick={runAllTests}>
                    ▶ Run matrix
                  </button>
                  <button className="btn" onClick={() => setResults({})}>
                    ✕ Clear
                  </button>
                </div>
              </div>
              <div className="matrix-table-wrap">
                {endpoints.length === 0 || environments.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">⊞</div>
                    Add endpoints and environments to build your matrix
                  </div>
                ) : (
                  <table className="matrix">
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left' }}>Endpoint</th>
                        {columns.map(col => {
                          const c = COLOR_MAP[col.color] || COLOR_MAP.cyan;
                          return (
                            <th key={col.id} className="env-header" style={{ color: c.text, background: c.bg, border: `1px solid ${c.border}` }}>
                              {col.label}
                            </th>
                          );
                        })}
                      </tr>
                    </thead>
                    <tbody>
                      {endpoints.map(ep => {
                        const mcls = { GET: 'get-m', POST: 'post-m', PUT: 'put-m', DELETE: 'del-m', PATCH: 'patch-m' }[ep.method] || 'get-m';
                        return (
                          <tr key={ep.id}>
                            <td className="row-label">
                              <span className={`rl-method ${mcls}`}>{ep.method}</span>
                              <span className="rl-path">{ep.path}</span>
                            </td>
                            {columns.map(col => (
                              <MatrixCell key={`${ep.id}-${col.id}`} endpoint={ep} col={col} />
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* BUILDER VIEW */}
          {currentView === 'builder' && (
            <div style={{ flex: 1, overflow: 'auto', padding: '16px', color: 'var(--text2)' }}>
              <p style={{ color: 'var(--text3)', marginBottom: '16px' }}>Request builder coming soon...</p>
            </div>
          )}

          {/* RESULTS PANEL */}
          <div className="main-bottom">
            <div className="results-tabs">
              <div className={`rtab ${resultPane === 'response' ? 'active' : ''}`} onClick={() => setResultPane('response')}>
                Response
              </div>
              <div className={`rtab ${resultPane === 'log' ? 'active' : ''}`} onClick={() => setResultPane('log')}>
                Test Log
              </div>
            </div>
            <div className="results-body">
              {resultPane === 'response' && (
                <div className="result-pane active">
                  {!activeResult ? (
                    <div className="empty-state" style={{ height: '160px' }}>
                      <div className="empty-icon">○</div>
                      Send a request or run a matrix cell to see the response
                    </div>
                  ) : (
                    <div>
                      <div className="response-meta">
                        <div className="resp-stat">
                          <div className="resp-stat-val" style={{ color: activeResult.pass ? 'var(--green)' : 'var(--red)' }}>
                            {activeResult.error ? 'ERR' : activeResult.status}
                          </div>
                          <div className="resp-stat-label">Status</div>
                        </div>
                        <div className="resp-stat">
                          <div className="resp-stat-val">{activeResult.duration || 0}ms</div>
                          <div className="resp-stat-label">Time</div>
                        </div>
                        <div className="resp-stat">
                          <div className="resp-stat-val">{activeResult.envName || '—'}</div>
                          <div className="resp-stat-label">Env</div>
                        </div>
                      </div>
                      <div className="json-viewer">
                        {activeResult.error ? (
                          <span style={{ color: 'var(--red)' }}>{activeResult.error}</span>
                        ) : (
                          <pre dangerouslySetInnerHTML={{ __html: syntaxHighlight(JSON.stringify(activeResult.body, null, 2)) }} />
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {resultPane === 'log' && (
                <div className="result-pane active">
                  <div className="test-log" ref={logEndRef}>
                    {logs.map((entry, idx) => (
                      <LogEntry key={idx} entry={entry} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* MODALS */}
      <Modal title="Add Endpoint" open={showEndpointModal} onClose={() => setShowEndpointModal(false)}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
          <div>
            <label className="form-label">HTTP Method</label>
            <select
              className="input"
              value={editingModal.method}
              onChange={e => setEditingModal({ ...editingModal, method: e.target.value })}
              style={{ width: '100%' }}
            >
              <option>GET</option>
              <option>POST</option>
              <option>PUT</option>
              <option>DELETE</option>
              <option>PATCH</option>
            </select>
          </div>
          <div>
            <label className="form-label">Name</label>
            <input
              className="input"
              value={editingModal.name}
              onChange={e => setEditingModal({ ...editingModal, name: e.target.value })}
              placeholder="Get Users"
              style={{ width: '100%' }}
            />
          </div>
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label className="form-label">Path</label>
          <input
            className="input"
            value={editingModal.path}
            onChange={e => setEditingModal({ ...editingModal, path: e.target.value })}
            placeholder="/api/users"
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
          <div>
            <label className="form-label">Auth Type</label>
            <select
              className="input"
              value={editingModal.auth}
              onChange={e => setEditingModal({ ...editingModal, auth: e.target.value })}
              style={{ width: '100%' }}
            >
              <option value="none">None</option>
              <option value="bearer">Bearer Token</option>
              <option value="basic">Basic Auth</option>
              <option value="apikey">API Key</option>
            </select>
          </div>
          <div>
            <label className="form-label">Expected Codes</label>
            <input
              className="input"
              value={editingModal.expectedCodes}
              onChange={e => setEditingModal({ ...editingModal, expectedCodes: e.target.value })}
              placeholder="200, 201"
              style={{ width: '100%' }}
            />
          </div>
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label className="form-label">Request Body (optional)</label>
          <textarea
            className="textarea"
            value={editingModal.body}
            onChange={e => setEditingModal({ ...editingModal, body: e.target.value })}
            placeholder='{"key":"value"}'
            style={{ width: '100%', minHeight: '80px' }}
          />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label className="form-label">Environments</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
            {environments.map(env => (
              <label key={env.id} style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '4px 8px', background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: '3px', cursor: 'pointer', fontSize: '11px' }}>
                <input
                  type="checkbox"
                  checked={editingModal.envIds.includes(env.id)}
                  onChange={e => {
                    if (e.target.checked) {
                      setEditingModal({ ...editingModal, envIds: [...editingModal.envIds, env.id] });
                    } else {
                      setEditingModal({ ...editingModal, envIds: editingModal.envIds.filter(id => id !== env.id) });
                    }
                  }}
                />
                <span>{env.name}</span>
              </label>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', marginTop: '18px', justifyContent: 'flex-end' }}>
          <button className="btn" onClick={() => setShowEndpointModal(false)}>
            Cancel
          </button>
          <button className="btn btn-cyan" onClick={saveEndpoint}>
            Add Endpoint
          </button>
        </div>
      </Modal>

      <Modal title="Add Environment" open={showEnvModal} onClose={() => setShowEnvModal(false)}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
          <div>
            <label className="form-label">Name</label>
            <input
              className="input"
              value={editingEnvModal.name}
              onChange={e => setEditingEnvModal({ ...editingEnvModal, name: e.target.value })}
              placeholder="staging"
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label className="form-label">Color</label>
            <select className="input" value={editingEnvModal.color} onChange={e => setEditingEnvModal({ ...editingEnvModal, color: e.target.value })} style={{ width: '100%' }}>
              <option value="cyan">Cyan</option>
              <option value="green">Green</option>
              <option value="amber">Amber</option>
              <option value="red">Red</option>
              <option value="purple">Purple</option>
              <option value="blue">Blue</option>
            </select>
          </div>
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label className="form-label">Base URL</label>
          <input
            className="input"
            value={editingEnvModal.baseUrl}
            onChange={e => setEditingEnvModal({ ...editingEnvModal, baseUrl: e.target.value })}
            placeholder="https://staging.api.example.com"
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label className="form-label">Default Auth Token (optional)</label>
          <input
            className="input"
            value={editingEnvModal.token}
            onChange={e => setEditingEnvModal({ ...editingEnvModal, token: e.target.value })}
            placeholder="Bearer eyJ..."
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label className="form-label">Headers (JSON, optional)</label>
          <textarea
            className="textarea"
            value={editingEnvModal.headers}
            onChange={e => setEditingEnvModal({ ...editingEnvModal, headers: e.target.value })}
            placeholder='{"X-API-Version":"2"}'
            style={{ width: '100%', minHeight: '60px' }}
          />
        </div>
        <div style={{ display: 'flex', gap: '8px', marginTop: '18px', justifyContent: 'flex-end' }}>
          <button className="btn" onClick={() => setShowEnvModal(false)}>
            Cancel
          </button>
          <button className="btn btn-cyan" onClick={saveEnvironment}>
            Add Environment
          </button>
        </div>
      </Modal>

      <Modal title="Import Collection" open={showImportModal} onClose={() => setShowImportModal(false)}>
        <div style={{ marginBottom: '10px' }}>
          <label className="form-label">Paste Postman/OpenAPI JSON or endpoint list</label>
          <textarea
            className="textarea"
            value={importText}
            onChange={e => setImportText(e.target.value)}
            placeholder='[{"method":"GET","path":"/api/users","name":"List Users"},...]'
            style={{ width: '100%', minHeight: '120px' }}
          />
        </div>
        <div style={{ display: 'flex', gap: '8px', marginTop: '18px', justifyContent: 'flex-end' }}>
          <button className="btn" onClick={() => setShowImportModal(false)}>
            Cancel
          </button>
          <button className="btn btn-cyan" onClick={doImport}>
            Import
          </button>
        </div>
      </Modal>

      {/* SUMMARY MODAL */}
      {showSummaryModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={() => setShowSummaryModal(false)}
        >
          <div
            className="modal"
            style={{ minWidth: '480px' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700' }}>📊 Test Execution Summary</h3>
              <button
                onClick={() => setShowSummaryModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text3)',
                  cursor: 'pointer',
                  fontSize: '20px',
                  padding: '4px 8px',
                  transition: 'color 0.15s'
                }}
                onMouseEnter={(e) => e.target.style.color = 'var(--text2)'}
                onMouseLeave={(e) => e.target.style.color = 'var(--text3)'}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
              <div
                style={{
                  padding: '16px',
                  background: 'var(--bg3)',
                  borderRadius: '6px',
                  border: '1px solid rgba(74,222,128,0.25)',
                  textAlign: 'center'
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px', fontWeight: '600' }}>Passed</div>
                <div style={{ fontSize: '32px', fontWeight: '700', color: 'var(--green)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {summaryPass}
                </div>
              </div>
              <div
                style={{
                  padding: '16px',
                  background: 'var(--bg3)',
                  borderRadius: '6px',
                  border: '1px solid rgba(248,113,113,0.25)',
                  textAlign: 'center'
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px', fontWeight: '600' }}>Failed</div>
                <div style={{ fontSize: '32px', fontWeight: '700', color: 'var(--red)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {summaryFail}
                </div>
              </div>
              <div
                style={{
                  padding: '16px',
                  background: 'var(--bg3)',
                  borderRadius: '6px',
                  border: '1px solid rgba(251,191,36,0.25)',
                  textAlign: 'center'
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px', fontWeight: '600' }}>Pending</div>
                <div style={{ fontSize: '32px', fontWeight: '700', color: 'var(--amber)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {summaryPending}
                </div>
              </div>
              <div
                style={{
                  padding: '16px',
                  background: 'var(--bg3)',
                  borderRadius: '6px',
                  border: '1px solid rgba(96,165,250,0.25)',
                  textAlign: 'center'
                }}
              >
                <div style={{ fontSize: '11px', color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px', fontWeight: '600' }}>Total Tests</div>
                <div style={{ fontSize: '32px', fontWeight: '700', color: 'var(--blue)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {summaryPass + summaryFail + summaryPending}
                </div>
              </div>
            </div>

            <div style={{ paddingTop: '16px', paddingBottom: '8px', borderTop: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', fontSize: '12px', borderBottom: '1px solid var(--border3)' }}>
                <span style={{ color: 'var(--text3)' }}>Pass Rate</span>
                <span
                  style={{
                    color: summaryPass + summaryFail > 0 ? 'var(--text1)' : 'var(--text3)',
                    fontWeight: '600',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '13px'
                  }}
                >
                  {summaryPass + summaryFail > 0
                    ? `${Math.round((summaryPass / (summaryPass + summaryFail)) * 100)}%`
                    : '—'}
                </span>
              </div>

              {lastRunTime && (
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', fontSize: '12px' }}>
                  <span style={{ color: 'var(--text3)' }}>Last Run</span>
                  <span style={{ color: 'var(--text1)', fontweight: '600', fontFamily: 'JetBrains Mono, monospace', fontSize: '11px' }}>
                    {lastRunTime}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

