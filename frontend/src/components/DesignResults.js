import React from 'react';
import { CheckCircle, AlertTriangle, XCircle, Loader } from 'lucide-react';

const DesignResults = ({ design, simulation, vendors }) => {
  if (!design) return null;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="icon status-completed" />;
      case 'processing':
        return <Loader className="icon spinning" />;
      case 'failed':
        return <XCircle className="icon status-failed" />;
      default:
        return <AlertTriangle className="icon status-pending" />;
    }
  };

  return (
    <div className="design-results">
      {/* Design Status */}
      <div className="card">
        <h2 className="card-title">
          {getStatusIcon(design.status)}
          Design Status
        </h2>
        <div className="design-info">
          <p><strong>Design ID:</strong> {design.design_id}</p>
          <p><strong>Type:</strong> {design.design_type}</p>
          <p><strong>Status:</strong> {design.status}</p>
          <p><strong>Description:</strong> {design.description}</p>
        </div>
      </div>

      {/* Schematic */}
      {design.schematic && (
        <div className="card">
          <h2 className="card-title">Schematic</h2>
          
          <div className="schematic-section">
            <h3>Components</h3>
            <div className="component-list">
              {design.schematic.components.map((comp) => (
                <div key={comp.id} className="component-item">
                  <strong>{comp.id}</strong>: {comp.type} ({comp.value})
                </div>
              ))}
            </div>
          </div>

          <div className="schematic-section">
            <h3>Connections</h3>
            <div className="connection-list">
              {design.schematic.connections.map((conn, idx) => (
                <div key={idx} className="connection-item">
                  {conn.from.component}.{conn.from.pin} → {conn.to.component}.{conn.to.pin}
                </div>
              ))}
            </div>
          </div>

          {design.schematic.layout && (
            <div className="schematic-section">
              <h3>Layout</h3>
              <p>{design.schematic.layout}</p>
            </div>
          )}

          {design.schematic.specifications && (
            <div className="schematic-section">
              <h3>Specifications</h3>
              <div className="specifications">
                {Object.entries(design.schematic.specifications).map(([key, value]) => (
                  <p key={key}>
                    <strong>{key.replace(/_/g, ' ')}:</strong> {value}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Simulation Results */}
      {simulation && (
        <div className="card">
          <h2 className="card-title">Simulation Results</h2>
          
          {simulation.conflicts && simulation.conflicts.length > 0 && (
            <div className="alert alert-danger">
              <h4>Conflicts Detected:</h4>
              <ul>
                {simulation.conflicts.map((conflict, idx) => (
                  <li key={idx}>{conflict}</li>
                ))}
              </ul>
            </div>
          )}

          {simulation.warnings && simulation.warnings.length > 0 && (
            <div className="alert alert-warning">
              <h4>Warnings:</h4>
              <ul>
                {simulation.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {simulation.results && (
            <div className="simulation-results">
              <h4>Performance Metrics:</h4>
              {simulation.results.metrics && (
                <div className="metrics">
                  {Object.entries(simulation.results.metrics).map(([key, value]) => (
                    <p key={key}>
                      <strong>{key.replace(/_/g, ' ')}:</strong> {value}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Vendor Matching */}
      {vendors && vendors.vendors && vendors.vendors.length > 0 && (
        <div className="card">
          <h2 className="card-title">Manufacturing Vendors</h2>
          
          {vendors.recommended_vendor && (
            <div className="alert alert-success">
              <h4>Recommended: {vendors.recommended_vendor.name}</h4>
              <p>Price: ${vendors.recommended_vendor.price_per_unit}/unit</p>
              <p>Lead Time: {vendors.recommended_vendor.lead_time_days} days</p>
              <p>Rating: {vendors.recommended_vendor.rating}/5.0</p>
            </div>
          )}

          <div className="vendor-list">
            {vendors.vendors.map((vendor) => (
              <div key={vendor.vendor_id} className="vendor-item">
                <h4>{vendor.name}</h4>
                <p><strong>Price:</strong> ${vendor.price_per_unit}/unit</p>
                <p><strong>Lead Time:</strong> {vendor.lead_time_days} days</p>
                <p><strong>Rating:</strong> {vendor.rating}/5.0</p>
                <p><strong>Capabilities:</strong> {vendor.capabilities.join(', ')}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DesignResults;
