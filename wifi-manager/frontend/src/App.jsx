import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [networks, setNetworks] = useState([]);
  const [saved, setSaved] = useState([]);
  const [status, setStatus] = useState({});
  const [password, setPassword] = useState('');
  const [selected, setSelected] = useState('');

  const refresh = async () => {
    const [scanRes, savedRes, statusRes] = await Promise.all([
      axios.get('/api/scan'),
      axios.get('/api/saved'),
      axios.get('/api/status')
    ]);
    setNetworks(scanRes.data);
    setSaved(savedRes.data);
    setStatus(statusRes.data);
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, []);

  const connect = async (ssid) => {
    const pwd = prompt(`Enter password for ${ssid}`) || '';
    try {
      await axios.post('/api/connect', { ssid, password: pwd });
      alert("Connected!");
      refresh();
    } catch (err) {
      alert("Failed: " + err.response?.data?.detail);
    }
  };

  const forget = async (ssid) => {
    if (confirm(`Forget ${ssid}?`)) {
      await axios.delete(`/api/saved/${ssid}`);
      refresh();
    }
  };

  return (
    <div className="app">
      <h1>Raspberry Pi WiFi Manager</h1>
      
      {status.connected && (
        <div className="status connected">
          Connected to: <strong>{status.ssid}</strong> ({status.ip})
        </div>
      )}

      <button onClick={refresh}>Refresh Networks</button>

      <h2>Available Networks</h2>
      <div className="networks">
        {networks.map(net => (
          <div key={net.ssid} className="network">
            <div>
              <strong>{net.ssid}</strong> {net.in_use && "✓"}
              <span className="signal">Signal: {net.signal}%</span>
            </div>
            <button onClick={() => connect(net.ssid)}>
              {net.in_use ? "Reconnect" : "Connect"}
            </button>
          </div>
        ))}
      </div>

      <h2>Saved Networks</h2>
      <div className="networks">
        {saved.map(net => (
          <div key={net.ssid} className="network saved">
            <strong>{net.ssid}</strong>
            <button onClick={() => forget(net.ssid)}>Forget</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;