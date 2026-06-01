import React from 'react';
import { Activity, Server, Smartphone, LayoutDashboard } from 'lucide-react';
import { ReadyState } from 'react-use-websocket';

/* ── StatusChip ─────────────────────────────────────────────────────────── */
function StatusChip({ icon, label, ok, last = false }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      padding: '5px 12px',
      borderRight: last ? 'none' : '1px solid #E2E8F0',
    }}>
      {icon}
      <span style={{
        fontSize: '0.72rem',
        fontWeight: 600,
        color: ok ? '#059669' : '#94A3B8',
        letterSpacing: '0.01em',
      }}>
        {label}
      </span>
    </div>
  );
}

/* ── Header ──────────────────────────────────────────────────────────────── */
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
  const wsOpen     = readyState === ReadyState.OPEN;
  const appiumOn   = appiumStatus === 'running';

  return (
    <header className="app-header">

      {/* ── Left: brand or loaded app icon ── */}
      <div className="app-header-left">
        {appIcon ? (
          <img src={appIcon} alt="App icon" className="app-logo" />
        ) : (
          <div style={{
            width: '32px', height: '32px',
            background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
            borderRadius: '8px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 6px rgba(37,99,235,0.25)',
            flexShrink: 0,
          }}>
            <LayoutDashboard size={16} color="#fff" />
          </div>
        )}
        <div>
          <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0F172A', lineHeight: 1.2 }}>
            {appTitle || 'TAP / Android'}
          </div>
          {!appTitle && (
            <div style={{ fontSize: '0.65rem', color: '#94A3B8', marginTop: '1px' }}>
              Test Automation Platform
            </div>
          )}
        </div>
      </div>

      {/* ── Right: status chips + button ── */}
      <div className="status-cont">

        {/* Status chips row */}
        <div className="status-box">
          <StatusChip
            icon={<Smartphone size={15} color={isDeviceConnected ? '#059669' : '#DC2626'} />}
            label={isDeviceConnected ? 'Device Connected' : 'No Device'}
            ok={isDeviceConnected}
          />
          <StatusChip
            icon={<Server size={15} color={wsOpen ? '#059669' : '#DC2626'} />}
            label={wsOpen ? 'Server Online' : 'Offline'}
            ok={wsOpen}
          />
          <StatusChip
            icon={<Activity size={15} color={appiumOn ? '#059669' : '#94A3B8'} />}
            label={appiumOn ? 'Appium Active' : 'Appium Off'}
            ok={appiumOn}
            last
          />
        </div>

        {/* View UI Issues */}
        <button
          onClick={onToggleUiIssues}
          disabled={uiIssuesLoading}
          className="view-UI-button"
          title={uiIssuesOpen ? 'Close UI Screenshot Issues' : 'Open UI Screenshot Issues'}
          style={uiIssuesOpen ? {
            background: '#EFF6FF',
            color: '#2563EB',
            border: '1px solid #BFDBFE',
          } : {}}
        >
          {uiIssuesLoading ? 'Loading…' : uiIssuesOpen ? 'Close UI Issues' : 'View UI Issues'}
        </button>
      </div>
    </header>
  );
}
