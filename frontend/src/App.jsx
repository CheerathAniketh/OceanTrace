import { useState, useEffect } from 'react';
import MapView from './components/MapView';
import VesselRanking from './components/VesselRanking';
import './App.css';

const API_URL = 'http://localhost:8000/api/spill-result';

function App() {
  const [data, setData] = useState(null);
  const [selectedVesselId, setSelectedVesselId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(API_URL)
      .then(res => {
        if (!res.ok) throw new Error(`API returned ${res.status}`);
        return res.json();
      })
      .then(setData)
      .catch(err => setError(err.message));
  }, []);

  if (error) return <div className="status-message">Failed to load pipeline data: {error}</div>;
  if (!data) return <div className="status-message">Loading spill data...</div>;

  return (
    <div className="dashboard-container">
      <div className="map-section">
        <MapView data={data} selectedVesselId={selectedVesselId} />
      </div>
      <div className="panel-section">
        <VesselRanking
          vessels={data.vessels}
          selectedVesselId={selectedVesselId}
          onSelectVessel={setSelectedVesselId}
        />
      </div>
    </div>
  );
}

export default App;