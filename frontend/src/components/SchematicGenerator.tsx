import React, { useState } from 'react';
import { generateSchematic } from '../services/api';

interface SchematicGeneratorProps {
  onSchematicGenerated: (schematic: any) => void;
}

const SchematicGenerator: React.FC<SchematicGeneratorProps> = ({ onSchematicGenerated }) => {
  const [prompt, setPrompt] = useState('');
  const [designType, setDesignType] = useState('pcb');
  const [outputFormat, setOutputFormat] = useState('rtl');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const schematic = await generateSchematic(prompt, designType, outputFormat);
      onSchematicGenerated(schematic);
    } catch (err: any) {
      setError(err.message || 'Failed to generate schematic');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h2>🎨 Prompt-to-Schematic AI Engine</h2>
      <p>Describe your desired chip or board in natural language — the system generates architecture, RTL, or analog schematics in real time.</p>

      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="prompt">Design Description</label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Example: Create an ESP32-based IoT board with LoRa module, temperature sensor, LED indicators, and USB-C power input"
            rows={4}
          />
        </div>

        <div className="stats-grid">
          <div className="input-group">
            <label htmlFor="designType">Design Type</label>
            <select
              id="designType"
              value={designType}
              onChange={(e) => setDesignType(e.target.value)}
            >
              <option value="pcb">PCB</option>
              <option value="chip">Chip</option>
              <option value="analog">Analog</option>
              <option value="digital">Digital</option>
            </select>
          </div>

          <div className="input-group">
            <label htmlFor="outputFormat">Output Format</label>
            <select
              id="outputFormat"
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value)}
            >
              <option value="rtl">RTL</option>
              <option value="analog">Analog</option>
              <option value="mixed-signal">Mixed-Signal</option>
            </select>
          </div>
        </div>

        <button type="submit" className="btn-primary" disabled={loading || !prompt.trim()}>
          {loading ? 'Generating...' : '⚡ Generate Schematic'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}
    </div>
  );
};

export default SchematicGenerator;
