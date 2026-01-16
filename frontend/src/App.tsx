import React, { useState } from 'react';
import SchematicGenerator from './components/SchematicGenerator';
import SchematicViewer from './components/SchematicViewer';
import SimulationPanel from './components/SimulationPanel';
import VendorPanel from './components/VendorPanel';
import './App.css';

interface Schematic {
  id: string;
  components: any[];
  nets: any[];
  svg_preview?: string;
  confidence_score: number;
}

function App() {
  const [schematic, setSchematic] = useState<Schematic | null>(null);
  const [activeTab, setActiveTab] = useState<string>('generate');

  const handleSchematicGenerated = (newSchematic: Schematic) => {
    setSchematic(newSchematic);
    setActiveTab('view');
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>⚛️ Quantum AI PCB Builder</h1>
        <p>AI-powered PCB and chip design platform</p>
      </header>

      <nav className="app-nav">
        <button 
          className={activeTab === 'generate' ? 'active' : ''} 
          onClick={() => setActiveTab('generate')}
        >
          Generate Schematic
        </button>
        <button 
          className={activeTab === 'view' ? 'active' : ''} 
          onClick={() => setActiveTab('view')}
          disabled={!schematic}
        >
          View Schematic
        </button>
        <button 
          className={activeTab === 'simulate' ? 'active' : ''} 
          onClick={() => setActiveTab('simulate')}
          disabled={!schematic}
        >
          Simulation
        </button>
        <button 
          className={activeTab === 'vendors' ? 'active' : ''} 
          onClick={() => setActiveTab('vendors')}
          disabled={!schematic}
        >
          Vendors & Quotes
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'generate' && (
          <SchematicGenerator onSchematicGenerated={handleSchematicGenerated} />
        )}
        {activeTab === 'view' && schematic && (
          <SchematicViewer schematic={schematic} />
        )}
        {activeTab === 'simulate' && schematic && (
          <SimulationPanel schematicId={schematic.id} />
        )}
        {activeTab === 'vendors' && schematic && (
          <VendorPanel schematicId={schematic.id} />
        )}
      </main>

      <footer className="app-footer">
        <p>Quantum AI PCB Builder v1.0.0 | Powered by FastAPI & React</p>
      </footer>
    </div>
  );
}

export default App;
