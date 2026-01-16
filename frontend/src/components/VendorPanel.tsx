import React, { useState } from 'react';
import { matchVendors } from '../services/api';

interface VendorPanelProps {
  schematicId: string;
}

const VendorPanel: React.FC<VendorPanelProps> = ({ schematicId }) => {
  const [quantity, setQuantity] = useState(1000);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleMatchVendors = async () => {
    setLoading(true);
    setError(null);

    try {
      const matchResult = await matchVendors(schematicId, quantity);
      setResult(matchResult);
    } catch (err: any) {
      setError(err.message || 'Failed to match vendors');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="panel">
        <h2>🏭 Vendor Matching & Quoting</h2>
        <p>Find compatible foundries, packaging houses, and PCB assemblers with estimated pricing and delivery timelines.</p>

        <div className="stats-grid">
          <div className="input-group">
            <label htmlFor="quantity">Order Quantity</label>
            <input
              type="number"
              id="quantity"
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
              min={1}
            />
          </div>
        </div>

        <button 
          className="btn-primary" 
          onClick={handleMatchVendors}
          disabled={loading}
        >
          {loading ? 'Matching...' : '🔍 Find Vendors'}
        </button>

        {error && <div className="error">{error}</div>}
      </div>

      {result && (
        <>
          <div className="panel">
            <h2>✨ Recommended Vendor</h2>
            
            {result.recommended_vendor_id && (
              <>
                {(() => {
                  const recommended = result.matched_vendors.find((v: any) => v.id === result.recommended_vendor_id);
                  const quote = result.quotes.find((q: any) => q.vendor_id === result.recommended_vendor_id);
                  
                  return (
                    <div className="stats-grid">
                      <div className="stat-card">
                        <div className="value" style={{ fontSize: '1.5rem' }}>{recommended?.name}</div>
                        <div className="label">{recommended?.type}</div>
                      </div>
                      <div className="stat-card">
                        <div className="value">${quote?.price_per_unit?.toFixed(2)}</div>
                        <div className="label">Per Unit</div>
                      </div>
                      <div className="stat-card">
                        <div className="value">{quote?.lead_time_days} days</div>
                        <div className="label">Lead Time</div>
                      </div>
                      <div className="stat-card">
                        <div className="value">{result.estimated_delivery_date}</div>
                        <div className="label">Est. Delivery</div>
                      </div>
                    </div>
                  );
                })()}
              </>
            )}
          </div>

          <div className="panel">
            <h2>📋 All Quotes</h2>
            
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #0f3460' }}>
                  <th style={{ textAlign: 'left', padding: '0.75rem' }}>Vendor</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem' }}>Price/Unit</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem' }}>Setup Cost</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem' }}>Lead Time</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem' }}>Min Qty</th>
                </tr>
              </thead>
              <tbody>
                {result.quotes.map((quote: any, idx: number) => (
                  <tr 
                    key={idx} 
                    style={{ 
                      borderBottom: '1px solid #0f3460',
                      background: quote.vendor_id === result.recommended_vendor_id ? 'rgba(0, 217, 255, 0.1)' : 'transparent'
                    }}
                  >
                    <td style={{ padding: '0.75rem' }}>
                      {quote.vendor_name}
                      {quote.vendor_id === result.recommended_vendor_id && (
                        <span className="badge badge-success" style={{ marginLeft: '0.5rem' }}>BEST</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right', padding: '0.75rem' }}>${quote.price_per_unit.toFixed(2)}</td>
                    <td style={{ textAlign: 'right', padding: '0.75rem' }}>${quote.setup_cost.toFixed(0)}</td>
                    <td style={{ textAlign: 'right', padding: '0.75rem' }}>{quote.lead_time_days} days</td>
                    <td style={{ textAlign: 'right', padding: '0.75rem' }}>{quote.minimum_quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="panel">
            <h2>🏢 Matched Vendors</h2>
            
            <div className="stats-grid">
              {result.matched_vendors.map((vendor: any, idx: number) => (
                <div key={idx} className="stat-card" style={{ textAlign: 'left' }}>
                  <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>{vendor.name}</div>
                  <div style={{ color: '#666', fontSize: '0.875rem' }}>
                    <div>📍 {vendor.location}</div>
                    <div>🏷️ {vendor.type}</div>
                    <div>⏱️ {vendor.lead_time_days} days lead time</div>
                  </div>
                  <div style={{ marginTop: '0.5rem' }}>
                    {vendor.capabilities?.slice(0, 3).map((cap: string, capIdx: number) => (
                      <span 
                        key={capIdx} 
                        className="badge badge-success" 
                        style={{ marginRight: '0.25rem', marginBottom: '0.25rem', display: 'inline-block' }}
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default VendorPanel;
