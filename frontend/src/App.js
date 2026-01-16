import React, { useState } from 'react';
import DesignInput from './components/DesignInput';
import DesignResults from './components/DesignResults';
import { createDesign, getDesign, runSimulation, matchVendors } from './services/api';
import './App.css';
import { Cpu, Github } from 'lucide-react';

function App() {
  const [loading, setLoading] = useState(false);
  const [design, setDesign] = useState(null);
  const [simulation, setSimulation] = useState(null);
  const [vendors, setVendors] = useState(null);
  const [error, setError] = useState(null);

  const handleDesignSubmit = async (designData) => {
    setLoading(true);
    setError(null);
    setDesign(null);
    setSimulation(null);
    setVendors(null);

    try {
      // Create design
      const createResponse = await createDesign(designData);
      console.log('Design created:', createResponse);

      // Poll for design completion
      let designComplete = false;
      let attempts = 0;
      const maxAttempts = 20;

      while (!designComplete && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const designDetails = await getDesign(createResponse.design_id);
        console.log('Design status:', designDetails.status);
        
        if (designDetails.status === 'completed') {
          designComplete = true;
          setDesign(designDetails);

          // Run simulation
          console.log('Running simulation...');
          const simResult = await runSimulation({
            design_id: createResponse.design_id,
            simulation_type: 'full'
          });
          setSimulation(simResult);

          // Match vendors
          console.log('Matching vendors...');
          const vendorResult = await matchVendors({
            design_id: createResponse.design_id,
            quantity: 100
          });
          setVendors(vendorResult);
          
        } else if (designDetails.status === 'failed') {
          throw new Error('Design generation failed');
        }
        
        attempts++;
      }

      if (!designComplete) {
        throw new Error('Design generation timed out');
      }

    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="header">
        <div className="container">
          <h1 className="title">
            <Cpu className="icon" />
            Quantum AI PCB Builder
          </h1>
          <p className="subtitle">
            AI-guided chip and PCB design lab - Describe your hardware in natural language
          </p>
        </div>
      </header>

      <main className="container">
        {error && (
          <div className="alert alert-error">
            <strong>Error:</strong> {error}
          </div>
        )}

        <DesignInput onSubmit={handleDesignSubmit} loading={loading} />
        <DesignResults design={design} simulation={simulation} vendors={vendors} />
      </main>

      <footer className="footer">
        <div className="container">
          <p>
            Quantum AI PCB Builder - Full design-to-fabrication pipeline
            <a
              href="https://github.com/NaTo1000/Quantum-Ai-PCB-Builder"
              target="_blank"
              rel="noopener noreferrer"
              className="footer-link"
            >
              <Github className="icon" />
              GitHub
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
