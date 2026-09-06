import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MapView from './components/MapView';
import VesselRanking from './components/VesselRanking';
import SpillAnalytics from './components/SpillAnalytics';
import TimelineControls from './components/TimelineControls';
import DossierPanel from './components/DossierPanel';
import './App.css';

const API_URL = 'http://localhost:8000/api/spill-result?mode=real';

function App() {
  const [data, setData] = useState(null);
  const [selectedVesselId, setSelectedVesselId] = useState(null);

  useEffect(() => {
    fetch(API_URL)
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error('Failed to fetch spill data:', err));
  }, []);

  if (!data) return <div className="status-message">Loading spill data...</div>;

  const selectedVessel = data.vessels.find(v => v.vessel_id === selectedVesselId);

  return (
    <div className="dashboard-container">
      <div className="live-badge">EcoWave Analytics</div>
      
      {/* Map is background */}
      <motion.div 
        className="map-section"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
      >
        <MapView data={data} selectedVesselId={selectedVesselId} />
      </motion.div>

      {/* Analytics Panel */}
      <motion.div
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 100 }}
      >
        <SpillAnalytics data={data} />
      </motion.div>
      
      {/* The unified AnimatePresence for morphing right panel */}
      <AnimatePresence mode="wait">
        {selectedVesselId ? (
          <DossierPanel 
            key="dossier" 
            vessel={selectedVessel} 
            onClose={() => setSelectedVesselId(null)} 
          />
        ) : (
          <motion.div 
            key="ranking"
            className="panel-section glass-panel"
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 100, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 100, damping: 15 }}
            style={{ position: 'absolute', top: 20, right: 20, bottom: 20, width: 400, overflowY: 'auto' }}
          >
            <div style={{ padding: '24px 24px 10px 24px', borderBottom: '1px solid var(--panel-border)' }}>
              <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, letterSpacing: '0.5px' }}>
                OCEAN_TRACE v2.4
              </h1>
            </div>
            <VesselRanking
              vessels={data.vessels}
              selectedVesselId={selectedVesselId}
              onSelectVessel={setSelectedVesselId}
            />
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Timeline Panel */}
      <motion.div
        initial={{ y: 100, opacity: 0, x: '-50%' }}
        animate={{ y: 0, opacity: 1, x: '-50%' }}
        transition={{ delay: 0.4, type: 'spring', stiffness: 100 }}
        style={{ position: 'absolute', bottom: 24, left: '50%' }}
      >
        <TimelineControls data={data} />
      </motion.div>
    </div>
  );
}

export default App;