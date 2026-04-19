import React, { useState } from "react";
import "./NetworkConfig.css";

const presets = {
    "2G": { download: 0.1, upload: 0.05, latency: 500 },
    "3G": { download: 2, upload: 1, latency: 200 },
    "4G": { download: 20, upload: 10, latency: 50 },
    "5G": { download: 100, upload: 50, latency: 10 },
};

// Reusable label component with hover tooltip
const MetricLabel = ({ title, tooltip }) => (
    <div className="metric-label">
        <label>{title}</label>
        <div className="tooltip-container">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            <span className="tooltip-text">{tooltip}</span>
        </div>
    </div>
);

const NetworkConfig = ({ setNetworkConfig }) => {
    const [enabled, setEnabled] = useState(false);
    // Initialized with your specific values
    const [networkType, setNetworkType] = useState("Custom");
    const [download, setDownload] = useState(17.8);
    const [upload, setUpload] = useState(20.35);
    const [latency, setLatency] = useState(570);
    const [packetLoss, setPacketLoss] = useState(1.3);
    const [jitter, setJitter] = useState(0);

    const handlePreset = (type) => {
        const preset = presets[type];
        setNetworkType(type);
        setDownload(preset.download);
        setUpload(preset.upload);
        setLatency(preset.latency);
    };

    const handleApply = async () => {
        const config = {
            enabled,
            networkType,
            download: Number(download),
            upload: Number(upload),
            latency: Number(latency),
            packetLoss: Number(packetLoss),
            jitter: Number(jitter),
        };
        
        setNetworkConfig(config);

        try {
            const res = await fetch("http://localhost:8000/network-simulate/apply", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(config),
            });

            const data = await res.json();
            console.log("Backend Response:", data);
        } catch (err) {
            console.error("Error:", err);
        }
    };

    return (
        <div className="network-card">
            <div className="network-header">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12.55a11 11 0 0 1 14.08 0"></path>
                    <path d="M1.42 9a16 16 0 0 1 21.16 0"></path>
                    <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
                    <line x1="12" y1="20" x2="12.01" y2="20"></line>
                </svg>
                Network Profile
            </div>

            {/* Toggle */}
            <div className="form-section">
                <label className="toggle-label">
                    <div className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={enabled}
                            onChange={(e) => setEnabled(e.target.checked)}
                        />
                        <span className="slider"></span>
                    </div>
                    <span className="toggle-text">Enable Network Simulation</span>
                </label>
            </div>

            <div className={`config-body ${!enabled ? "disabled-state" : ""}`}>
                <div className="row horizontal">
                    {/* Network Type */}
                    <div className="control-group half">
                        <label>Network Type</label>
                        <select
                            value={networkType}
                            onChange={(e) => setNetworkType(e.target.value)}
                            disabled={!enabled}
                        >
                            <option>2G</option>
                            <option>3G</option>
                            <option>4G</option>
                            <option>5G</option>
                            <option>WiFi</option>
                            <option>Custom</option>
                        </select>
                    </div>

                    {/* Presets */}
                    <div className="control-group half">
                        <label>Quick Presets</label>
                        <div className="chips">
                            {Object.keys(presets).map((key) => (
                                <button
                                    key={key}
                                    disabled={!enabled}
                                    className={`chip ${networkType === key ? "active" : ""}`}
                                    onClick={() => handlePreset(key)}
                                >
                                    {key}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Advanced Settings */}
                <details className="advanced-settings">
                    <summary>Advanced Configuration</summary>
                    <div className="advanced-content">
                        <div className="slider-group">
                            <div className="slider-header">
                                <MetricLabel
                                    title="Download"
                                    tooltip="Speed at which data is received from the server."
                                />
                                <span>{download} Mbps</span>
                            </div>
                            <input type="range" min="0.1" max="100" step="0.1" value={download} onChange={(e) => setDownload(e.target.value)} disabled={!enabled} />
                        </div>

                        <div className="slider-group">
                            <div className="slider-header">
                                <MetricLabel
                                    title="Upload"
                                    tooltip="Speed at which data is sent to the server."
                                />
                                <span>{upload} Mbps</span>
                            </div>
                            <input type="range" min="0.05" max="50" step="0.1" value={upload} onChange={(e) => setUpload(e.target.value)} disabled={!enabled} />
                        </div>

                        <div className="slider-group">
                            <div className="slider-header">
                                <MetricLabel
                                    title="Latency"
                                    tooltip="Delay before a transfer of data begins (ping)."
                                />
                                <span>{latency} ms</span>
                            </div>
                            <input type="range" min="0" max="1000" step="10" value={latency} onChange={(e) => setLatency(e.target.value)} disabled={!enabled} />
                        </div>

                        <div className="slider-group">
                            <div className="slider-header">
                                <MetricLabel
                                    title="Packet Loss"
                                    tooltip="Percentage of data packets that fail to arrive."
                                />
                                <span>{packetLoss}%</span>
                            </div>
                            <input type="range" min="0" max="10" step="0.1" value={packetLoss} onChange={(e) => setPacketLoss(e.target.value)} disabled={!enabled} />
                        </div>

                        <div className="slider-group">
                            <div className="slider-header">
                                <MetricLabel
                                    title="Jitter"
                                    tooltip="The variation in the delay of received packets."
                                />
                                <span>{jitter} ms</span>
                            </div>
                            <input type="range" min="0" max="200" step="5" value={jitter} onChange={(e) => setJitter(e.target.value)} disabled={!enabled} />
                        </div>
                    </div>
                </details>
            </div>

            {/* Apply */}
            <button className="btn-primary" disabled={!enabled} onClick={handleApply}>
                Apply Configuration
            </button>
        </div>
    );
};

export default NetworkConfig;