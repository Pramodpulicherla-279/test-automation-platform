import React, { useState, useEffect, useRef } from 'react';
import { Upload, Play, Download, X, Check, AlertCircle, Clock } from 'lucide-react';
import './APIBatchTester.css';

const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/test-status';

const ts = () => {
  const n = new Date();
  return `${String(n.getHours()).padStart(2, '0')}:${String(n.getMinutes()).padStart(2, '0')}:${String(n.getSeconds()).padStart(2, '0')}.${String(n.getMilliseconds()).padStart(3, '0')}`;
};

export default function APIBatchTester() {
  const [baseUrl, setBaseUrl] = useState('http://localhost:3000');
  const [parsedAPIs, setParsedAPIs] = useState([]);
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState(null);
  const [logs, setLogs] = useState([]);
  const [running, setRunning] = useState(false);
  const [currentView, setCurrentView] = useState('upload'); // upload, preview, results, monitoring
  const [fileSelected, setFileSelected] = useState(null);
  const [timeout, setTimeout] = useState(10000);
  const [iframeUrl, setIframeUrl] = useState('http://localhost:8000/static/grafana.html');
  const [showIframeSettings, setShowIframeSettings] = useState(false);
  const [tempIframeUrl, setTempIframeUrl] = useState('http://localhost:8000/static/grafana.html');
  const logEndRef = useRef(null);
  const wsRef = useRef(null);

  // Auto-scroll logs
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollTop = logEndRef.current.scrollHeight;
    }
  }, [logs]);

  // Connect to WebSocket
  useEffect(() => {
    wsRef.current = new WebSocket(WS_URL);
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'BATCH_API_TEST') {
        const { action, total, index, result, summary: newSummary } = data.payload;
        
        if (action === 'test_start') {
          appendLog('INFO', `Starting batch API tests... (Total: ${total})`);
          setResults([]);
          setSummary(null);
        } else if (action === 'test_progress') {
          setResults(prev => {
            const updated = [...prev];
            updated[index - 1] = result;
            return updated;
          });
          const status = result.passed ? '✓ PASS' : '✗ FAIL';
          appendLog(result.passed ? 'SUCCESS' : 'FAILED', 
            `[${index}/${total}] ${result.method} ${result.endpoint} - Status: ${result.status} ${status}`);
        } else if (action === 'test_complete') {
          setSummary(newSummary);
          appendLog('INFO', 
            `Batch tests completed! Passed: ${newSummary.passed}/${newSummary.total}, Duration: ${newSummary.duration}ms`);
          setRunning(false);
          setCurrentView('results');
        }
      }
    };
    
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const appendLog = (level, msg) => {
    setLogs(prev => [
      { level, msg, time: ts() },
      ...prev.slice(0, 499)
    ]);
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setFileSelected(file.name);
    appendLog('INFO', `File selected: ${file.name}`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      appendLog('INFO', 'Parsing Excel file...');
      const response = await fetch(`${API_URL}/api/batch/parse-excel`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      setParsedAPIs(data.apis || []);
      appendLog('SUCCESS', `Parsed ${data.count} APIs from Excel`);
      setCurrentView('preview');
    } catch (error) {
      appendLog('FAILED', `Failed to parse Excel: ${error.message}`);
    }
  };

  const handleRunTests = async () => {
    if (!parsedAPIs.length) {
      appendLog('FAILED', 'No APIs to test');
      return;
    }

    if (!baseUrl.trim()) {
      appendLog('FAILED', 'Base URL is required');
      return;
    }

    setRunning(true);
    setResults([]);
    setSummary(null);
    appendLog('INFO', `Running ${parsedAPIs.length} API tests...`);

    try {
      const response = await fetch(`${API_URL}/api/batch/run-tests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_url: baseUrl,
          apis: parsedAPIs,
          timeout: timeout,
        }),
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      // Results will come via WebSocket
    } catch (error) {
      appendLog('FAILED', `Test execution failed: ${error.message}`);
      setRunning(false);
    }
  };

  const handleDownloadSampleExcel = async () => {
    try {
      appendLog('INFO', 'Downloading sample Excel template...');
      const response = await fetch(`${API_URL}/api/batch/sample-excel`);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server error: ${response.status} - ${errorText}`);
      }

      const blob = await response.blob();
      
      if (blob.size === 0) {
        throw new Error('Downloaded file is empty');
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'api_batch_template.xlsx';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      appendLog('SUCCESS', 'Sample template downloaded successfully');
    } catch (error) {
      console.error('Download error:', error);
      appendLog('FAILED', `Download failed: ${error.message}`);
    }
  };

  const handleExportResults = () => {
    if (!results.length) {
      appendLog('FAILED', 'No results to export');
      return;
    }

    const csv = [
      ['API Name', 'Method', 'Endpoint', 'Status', 'Expected', 'Passed', 'Duration', 'Error', 'Timestamp'].join(','),
      ...results.map(r => [
        `"${r.api_name}"`,
        r.method,
        `"${r.endpoint}"`,
        r.status || 'N/A',
        r.expected.join(';'),
        r.passed ? 'YES' : 'NO',
        r.duration,
        r.error ? `"${r.error}"` : '',
        r.timestamp,
      ].join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api_batch_results_${new Date().getTime()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    appendLog('SUCCESS', 'Results exported to CSV');
  };

  const renderUploadView = () => (
    <div className="batch-tester-panel upload-view">
      <div className="upload-section">
        <div className="upload-box">
          <Upload size={48} strokeWidth={1.5} />
          <h3>Upload API List (Excel)</h3>
          <p>Select an Excel file with your API configurations</p>
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileSelect}
            disabled={running}
            className="file-input"
          />
          <p className="file-selected">{fileSelected ? `Selected: ${fileSelected}` : 'No file selected'}</p>
        </div>

        <div className="setup-section">
          <h4>Test Configuration</h4>
          <div className="form-group">
            <label>Base URL:</label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:3000"
              disabled={running}
            />
          </div>
          <div className="form-group">
            <label>Timeout (ms):</label>
            <input
              type="number"
              value={timeout}
              onChange={(e) => setTimeout(Math.max(1000, parseInt(e.target.value) || 10000))}
              min={1000}
              disabled={running}
            />
          </div>
          <button onClick={handleDownloadSampleExcel} disabled={running} className="btn-secondary">
            <Download size={16} />
            Download Sample Template
          </button>
        </div>
      </div>
    </div>
  );

  const renderPreviewView = () => (
    <div className="batch-tester-panel preview-view">
      <div className="preview-header">
        <h3>Preview APIs ({parsedAPIs.length})</h3>
        <button onClick={() => setCurrentView('upload')} className="btn-icon">
          <X size={16} />
        </button>
      </div>

      <div className="api-list">
        {parsedAPIs.map((api, idx) => (
          <div key={idx} className="api-item">
            <div className="api-method" style={{ color: getMethodColor(api.method) }}>
              {api.method}
            </div>
            <div className="api-details">
              <div className="api-name">{api.api_name}</div>
              <div className="api-endpoint">{api.endpoint}</div>
              <div className="api-meta">
                {api.description && <span>{api.description}</span>}
                {api.expected_status && <span>Status: {api.expected_status.join(', ')}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="preview-actions">
        <button 
          onClick={handleRunTests} 
          disabled={running || !parsedAPIs.length}
          className="btn-primary"
        >
          <Play size={16} />
          Run Tests
        </button>
      </div>
    </div>
  );

  const renderResultsView = () => (
    <div className="batch-tester-panel results-view">
      <div className="results-header">
        <h3>Test Results</h3>
        <div className="results-summary">
          {summary && (
            <>
              <span className="summary-item passed">✓ {summary.passed} Passed</span>
              <span className="summary-item failed">✗ {summary.failed} Failed</span>
              <span className="summary-item total">Total: {summary.total}</span>
              <span className="summary-item duration">⏱ {summary.duration}ms</span>
            </>
          )}
        </div>
      </div>

      <div className="results-table">
        <div className="table-header">
          <div className="col-status">Status</div>
          <div className="col-api">API Name</div>
          <div className="col-method">Method</div>
          <div className="col-endpoint">Endpoint</div>
          <div className="col-http">HTTP</div>
          <div className="col-duration">Duration</div>
        </div>

        <div className="table-body">
          {results.map((result, idx) => (
            <div key={idx} className={`table-row ${result.passed ? 'success' : 'failure'}`}>
              <div className="col-status">
                {result.passed ? <Check size={16} /> : <AlertCircle size={16} />}
              </div>
              <div className="col-api">{result.api_name}</div>
              <div className="col-method" style={{ color: getMethodColor(result.method) }}>
                {result.method}
              </div>
              <div className="col-endpoint">{result.endpoint}</div>
              <div className="col-http">{result.status || 'ERR'}</div>
              <div className="col-duration">{result.duration}ms</div>
            </div>
          ))}
        </div>
      </div>

      <div className="results-actions">
        <button onClick={handleExportResults} className="btn-secondary">
          <Download size={16} />
          Export CSV
        </button>
        <button 
          onClick={() => {
            setCurrentView('upload');
            setParsedAPIs([]);
            setResults([]);
            setSummary(null);
          }} 
          className="btn-secondary"
        >
          Run Another Test
        </button>
      </div>
    </div>
  );

  const renderMonitoringView = () => (
    <div className="batch-tester-panel monitoring-view">
      <div className="monitoring-header">
        <h3>Monitoring Dashboard</h3>
        <button 
          onClick={() => setShowIframeSettings(!showIframeSettings)}
          className="btn-icon"
          title="Configure Dashboard URL"
        >
          ⚙️
        </button>
      </div>

      {showIframeSettings && (
        <div className="iframe-settings">
          <div className="settings-group">
            <label>Dashboard URL:</label>
            <input
              type="text"
              value={tempIframeUrl}
              onChange={(e) => setTempIframeUrl(e.target.value)}
              placeholder="https://your-dashboard.com"
              className="url-input"
            />
          </div>
          <div className="settings-actions">
            <button
              onClick={() => {
                setIframeUrl(tempIframeUrl);
                setShowIframeSettings(false);
                appendLog('INFO', 'Dashboard URL updated successfully');
              }}
              className="btn-primary"
            >
              Apply
            </button>
            <button
              onClick={() => {
                setTempIframeUrl(iframeUrl);
                setShowIframeSettings(false);
              }}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="iframe-container">
        <iframe
          src={iframeUrl}
          title="Monitoring Dashboard"
          className="dashboard-iframe"
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
        />
      </div>
    </div>
  );

  const renderLogs = () => (
    <div className="logs-panel">
      <h4>Execution Logs</h4>
      <div className="logs-content" ref={logEndRef}>
        {logs.length === 0 ? (
          <div className="log-entry empty">No logs yet...</div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} className={`log-entry ${log.level.toLowerCase()}`}>
              <span className="log-time">{log.time}</span>
              <span className="log-level">{log.level}</span>
              <span className="log-msg">{log.msg}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );

  return (
    <div className="api-batch-tester">
      <div className="batch-header">
        <h2>API Batch Tester</h2>
        <p>Test multiple APIs using Excel configuration</p>
        <div className="view-tabs">
          <button
            className={`view-tab ${currentView === 'upload' ? 'active' : ''}`}
            onClick={() => setCurrentView('upload')}
          >
            Upload
          </button>
          <button
            className={`view-tab ${currentView === 'results' ? 'active' : ''}`}
            onClick={() => setCurrentView('results')}
            disabled={!results.length}
          >
            Results
          </button>
          <button
            className={`view-tab ${currentView === 'monitoring' ? 'active' : ''}`}
            onClick={() => setCurrentView('monitoring')}
          >
            📊 Monitoring
          </button>
        </div>
      </div>

      <div className="batch-container">
        <div className="batch-main">
          {currentView === 'upload' && renderUploadView()}
          {currentView === 'preview' && renderPreviewView()}
          {currentView === 'results' && renderResultsView()}
          {currentView === 'monitoring' && renderMonitoringView()}
        </div>

        <div className="batch-sidebar">
          {renderLogs()}
        </div>
      </div>
    </div>
  );
}

function getMethodColor(method) {
  const colors = {
    GET: '#008000',
    POST: '#0066cc',
    PUT: '#ff8800',
    DELETE: '#cc0000',
    PATCH: '#9933cc',
    HEAD: '#666666',
    OPTIONS: '#663399',
  };
  return colors[method] || '#333333';
}
