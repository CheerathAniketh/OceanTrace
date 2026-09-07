import React from 'react';
import { X, Navigation } from 'lucide-react';
import { motion } from 'framer-motion';

export default function DossierPanel({ vessel, onClose }) {
  if (!vessel) return null;

  return (
    <motion.div 
      className="dossier-panel glass-panel"
      layoutId={`vessel-${vessel.vessel_id}`}
      initial={{ borderRadius: 12 }}
      animate={{ borderRadius: 20 }}
    >
      <div className="dossier-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Navigation size={24} className="icon-accent-blue" />
          <div>
            <h2 style={{ margin: 0, fontSize: '1.4rem' }}>{vessel.name.toUpperCase()}</h2>
            <div className="vessel-imo" style={{ opacity: 0.7 }}>Vessel ID: {vessel.vessel_id}</div>
          </div>
        </div>
        <button className="close-btn" onClick={onClose}><X size={24} /></button>
      </div>

      <div className="dossier-grid">
        <div className="dossier-box full-width">
          <h3 className="box-title">SUSPICION BREAKDOWN</h3>
          <div className="metric-grid">
            <div className="metric-box">
              <div className="metric-title"><span>Overall Suspicion</span></div>
              <div className="metric-value highlight-red">
                {Math.round(vessel.score * 100)}<span className="metric-unit">%</span>
              </div>
            </div>
            <div className="metric-box">
              <div className="metric-title"><span>Proximity</span></div>
              <div className="metric-value text-small">
                {Math.round(vessel.proximity_score * 100)}%
              </div>
            </div>
            <div className="metric-box">
              <div className="metric-title"><span>Trajectory Match</span></div>
              <div className="metric-value text-small">
                {Math.round(vessel.trajectory_score * 100)}%
              </div>
            </div>
            <div className="metric-box">
              <div className="metric-title"><span>Anomaly Score</span></div>
              <div className="metric-value text-small">
                {Math.round(vessel.anomaly_score * 100)}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}