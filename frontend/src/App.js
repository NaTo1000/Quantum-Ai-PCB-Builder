import React, { useState } from 'react';

function App() {
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('');
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('Processing...');

    try {
      const response = await fetch('/api/design', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ description }),
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        setStatus('Design generated successfully!');
      } else {
        setStatus('Error generating design');
      }
    } catch (error) {
      setStatus('Error: ' + error.message);
    }
  };

  return (
    <div className="App">
      <header>
        <h1>Quantum-Ai-PCB-Builder</h1>
        <p>AI-Guided Chip and PCB Design Lab</p>
      </header>

      <main>
        <section className="design-input">
          <h2>Describe Your Hardware</h2>
          <form onSubmit={handleSubmit}>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your desired hardware design in natural language..."
              rows={6}
            />
            <button type="submit">Generate Design</button>
          </form>
        </section>

        {status && <p className="status">{status}</p>}

        {result && (
          <section className="design-result">
            <h2>Design Result</h2>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </section>
        )}
      </main>

      <footer>
        <p>Powered by AI and EDA tools</p>
      </footer>
    </div>
  );
}

export default App;
