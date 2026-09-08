import React from 'react';
import { X, Navigation, MapPin } from 'lucide-react';
import { motion } from 'framer-motion';
import { riskTier } from '../utils/riskTier';

function formatTimestamp(iso) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export default function DossierPanel({ vessel, onClose }) {
  if (!vessel) return null;

  const overallScore = Math.round(vessel.score * 100);
  const tier = riskTier(overallScore);

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
              <div className="metric-value" style={{ color: tier.color }}>
                {overallScore}<span className="metric-unit">%</span>
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

        <div className="dossier-box full-width">
          <h3 className="box-title">TRACK HISTORY</h3>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {vessel.track.map((point, i) => {
              const [lat, lon, timestamp] = point;
              const isLast = i === vessel.track.length - 1;
              return (
                <div
                  key={i}
                  className="profile-row"
                  style={{ borderBottom: isLast ? 'none' : undefined }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <MapPin size={14} className="icon-muted" />
                    <span>{lat.toFixed(4)}, {lon.toFixed(4)}</span>
                  </div>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    {formatTimestamp(timestamp)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </motion.div>
  );
}