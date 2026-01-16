import React, { useState } from 'react';
import { Cpu, Zap } from 'lucide-react';

const DesignInput = ({ onSubmit, loading }) => {
  const [description, setDescription] = useState('');
  const [designType, setDesignType] = useState('pcb');
  const [codeInput, setCodeInput] = useState('');
  const [showCodeInput, setShowCodeInput] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      description,
      design_type: designType,
      code_input: showCodeInput ? codeInput : null,
    });
  };

  return (
    <div className="design-input">
      <div className="card">
        <h2 className="card-title">
          <Cpu className="icon" />
          Create New Design
        </h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="designType">Design Type</label>
            <select
              id="designType"
              value={designType}
              onChange={(e) => setDesignType(e.target.value)}
              className="form-control"
            >
              <option value="pcb">PCB</option>
              <option value="chip">Chip</option>
              <option value="esp32">ESP32</option>
              <option value="lora">LoRa</option>
              <option value="custom">Custom</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="description">Design Description</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your hardware design in natural language..."
              rows="6"
              className="form-control"
              required
            />
            <small className="form-text">
              Example: "Create an ESP32-based temperature sensor with WiFi connectivity,
              DHT22 sensor, and battery power management"
            </small>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={showCodeInput}
                onChange={(e) => setShowCodeInput(e.target.checked)}
              />
              {' '}Add code-based specification
            </label>
          </div>

          {showCodeInput && (
            <div className="form-group">
              <label htmlFor="codeInput">Code Specification</label>
              <textarea
                id="codeInput"
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value)}
                placeholder="Enter technical specifications or constraints..."
                rows="4"
                className="form-control"
              />
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !description}
          >
            {loading ? (
              <>
                <Zap className="icon spinning" />
                Generating Design...
              </>
            ) : (
              <>
                <Zap className="icon" />
                Generate Design
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default DesignInput;
