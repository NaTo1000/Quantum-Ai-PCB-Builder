import React, { useState } from 'react';
import { runSimulation } from '../services/api';

interface SimulationPanelProps {
  schematicId: string;
}

const SimulationPanel: React.FC<SimulationPanelProps> = ({ schematicId }) => {
  const [simulationType, setSimulationType] = useState('spice');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunSimulation = async () => {
    setLoading(true);
    setError(null);

    try {
      const simResult = await runSimulation(schematicId, simulationType);
      setResult(simResult);
    } catch (err: any) {
      setError(err.message || 'Simulation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="panel">
        <h2>🔬 Simulation Pipeline</h2>
        <p>Run SPICE, timing, and power simulations with confidence scoring and visual feedback.</p>

        <div className="stats-grid">
          <div className="input-group">
            <label htmlFor="simType">Simulation Type</label>
            <select
              id="simType"
              value={simulationType}
              onChange={(e) => setSimulationType(e.target.value)}
            >
              <option value="spice">SPICE Analysis</option>
              <option value="timing">Timing Analysis</option>
              <option value="power">Power Analysis</option>
            </select>
          </div>
        </div>

        <button 
          className="btn-primary" 
          onClick={handleRunSimulation}
          disabled={loading}
        >
          {loading ? 'Running...' : '▶️ Run Simulation'}
        </button>

        {error && <div className="error">{error}</div>}
      </div>

      {result && (
        <div className="panel">
          <h2>📊 Simulation Results</h2>
          
          <div className="stats-grid">
            <div className="stat-card">
              <div className="value" style={{ color: result.result.status === 'completed' ? '#00ff88' : '#ff4444' }}>
                {result.result.status.toUpperCase()}
              </div>
              <div className="label">Status</div>
            </div>
            <div className="stat-card">
              <div className="value">{(result.result.confidence_score * 100).toFixed(0)}%</div>
              <div className="label">Confidence Score</div>
            </div>
          </div>

          {result.result.timing_report && (
            <div style={{ marginTop: '1rem' }}>
              <h4>⏱️ Timing Report</h4>
              <ul className="component-list">
                <li>
                  <span>Clock Frequency</span>
                  <span>{result.result.timing_report.clock_frequency}</span>
                </li>
                <li>
                  <span>Setup Time</span>
                  <span>{result.result.timing_report.setup_time}</span>
                </li>
                <li>
                  <span>Hold Time</span>
                  <span>{result.result.timing_report.hold_time}</span>
                </li>
                <li>
                  <span>Slack</span>
                  <span className={`badge ${result.result.timing_report.timing_met ? 'badge-success' : 'badge-error'}`}>
                    {result.result.timing_report.slack}
                  </span>
                </li>
              </ul>
            </div>
          )}

          {result.result.power_report && (
            <div style={{ marginTop: '1rem' }}>
              <h4>⚡ Power Report</h4>
              <ul className="component-list">
                <li>
                  <span>Total Power</span>
                  <span>{result.result.power_report.total_power_mw} mW</span>
                </li>
                <li>
                  <span>Current Draw</span>
                  <span>{result.result.power_report.current_ma?.toFixed(2) ?? 'N/A'} mA</span>
                </li>
                <li>
                  <span>Efficiency</span>
                  <span>{(result.result.power_report.efficiency * 100).toFixed(0)}%</span>
                </li>
                <li>
                  <span>Thermal Dissipation</span>
                  <span>{result.result.power_report.thermal_dissipation_mw?.toFixed(2) ?? 'N/A'} mW</span>
                </li>
              </ul>
            </div>
          )}

          {result.visual_feedback && (
            <div style={{ marginTop: '1rem' }}>
              <h4>📈 Waveforms</h4>
              <div className="schematic-preview" style={{ background: '#1a1a2e' }} dangerouslySetInnerHTML={{ __html: result.visual_feedback }} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SimulationPanel;
