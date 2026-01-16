import React, { useState, useEffect } from 'react';
import { runDesignChecks, generateBOM } from '../services/api';

interface SchematicViewerProps {
  schematic: {
    id: string;
    components: any[];
    nets: any[];
    svg_preview?: string;
    confidence_score: number;
  };
}

const SchematicViewer: React.FC<SchematicViewerProps> = ({ schematic }) => {
  const [checkResults, setCheckResults] = useState<any>(null);
  const [bom, setBom] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDesignChecks();
    loadBOM();
  }, [schematic.id]);

  const loadDesignChecks = async () => {
    try {
      const results = await runDesignChecks(schematic.id);
      setCheckResults(results);
    } catch (err) {
      console.error('Failed to load design checks:', err);
    }
  };

  const loadBOM = async () => {
    try {
      const bomData = await generateBOM(schematic.id);
      setBom(bomData);
    } catch (err) {
      console.error('Failed to load BOM:', err);
    }
  };

  return (
    <div>
      <div className="panel">
        <h2>📐 Schematic Preview</h2>
        
        <div className="stats-grid">
          <div className="stat-card">
            <div className="value">{schematic.components.length}</div>
            <div className="label">Components</div>
          </div>
          <div className="stat-card">
            <div className="value">{schematic.nets.length}</div>
            <div className="label">Nets</div>
          </div>
          <div className="stat-card">
            <div className="value">{(schematic.confidence_score * 100).toFixed(0)}%</div>
            <div className="label">Confidence Score</div>
          </div>
        </div>

        {schematic.svg_preview && (
          <div className="schematic-preview" dangerouslySetInnerHTML={{ __html: schematic.svg_preview }} />
        )}
      </div>

      <div className="panel">
        <h2>✅ Automated Design Checks</h2>
        <p>Built-in rule engines for DRC, LVS, thermal, and signal integrity checks.</p>
        
        {checkResults ? (
          <>
            <div className="stats-grid">
              <div className="stat-card">
                <span className={`badge ${checkResults.drc_passed ? 'badge-success' : 'badge-error'}`}>
                  {checkResults.drc_passed ? 'PASS' : 'FAIL'}
                </span>
                <div className="label">DRC</div>
              </div>
              <div className="stat-card">
                <span className={`badge ${checkResults.lvs_passed ? 'badge-success' : 'badge-error'}`}>
                  {checkResults.lvs_passed ? 'PASS' : 'FAIL'}
                </span>
                <div className="label">LVS</div>
              </div>
              <div className="stat-card">
                <span className={`badge ${checkResults.thermal_passed ? 'badge-success' : 'badge-warning'}`}>
                  {checkResults.thermal_passed ? 'PASS' : 'WARN'}
                </span>
                <div className="label">Thermal</div>
              </div>
              <div className="stat-card">
                <span className={`badge ${checkResults.signal_integrity_passed ? 'badge-success' : 'badge-warning'}`}>
                  {checkResults.signal_integrity_passed ? 'PASS' : 'WARN'}
                </span>
                <div className="label">Signal Integrity</div>
              </div>
            </div>

            {checkResults.violations && checkResults.violations.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <h4>Violations ({checkResults.violations.length})</h4>
                <ul className="component-list">
                  {checkResults.violations.map((v: any, idx: number) => (
                    <li key={idx}>
                      <span>{v.message}</span>
                      <span className={`badge badge-${v.severity === 'error' ? 'error' : v.severity === 'warning' ? 'warning' : 'success'}`}>
                        {v.severity.toUpperCase()}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div className="loading">Loading design checks...</div>
        )}
      </div>

      <div className="panel">
        <h2>📦 Bill of Materials</h2>
        
        {bom ? (
          <>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="value">{bom.total_components}</div>
                <div className="label">Total Components</div>
              </div>
              <div className="stat-card">
                <div className="value">${bom.estimated_cost?.toFixed(2) || '0.00'}</div>
                <div className="label">Estimated Cost</div>
              </div>
            </div>

            <ul className="component-list">
              {bom.items?.map((item: any, idx: number) => (
                <li key={idx}>
                  <span>
                    <strong>{item.component_spec.name}</strong>
                    <span style={{ color: '#666', marginLeft: '0.5rem' }}>
                      x{item.quantity}
                    </span>
                  </span>
                  <span>${item.total_price?.toFixed(2) || '0.00'}</span>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <div className="loading">Loading BOM...</div>
        )}
      </div>

      <div className="panel">
        <h2>🔧 Components</h2>
        <ul className="component-list">
          {schematic.components.map((comp, idx) => (
            <li key={idx}>
              <span>
                <strong>{comp.name}</strong>
                <span style={{ color: '#666', marginLeft: '0.5rem' }}>{comp.type}</span>
              </span>
              {comp.package && <span className="badge badge-success">{comp.package}</span>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default SchematicViewer;
