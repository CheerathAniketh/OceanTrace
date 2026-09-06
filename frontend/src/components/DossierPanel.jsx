import React from 'react';
import { X, Navigation, Activity, ShieldAlert, Radio } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';

export default function DossierPanel({ vessel, onClose }) {
  if (!vessel) return null;

  // Mock data stream for the chart
  const speedData = vessel.track.map((p, i) => ({
    time: i,
    speed: 10 + Math.random() * 5 - (i > 1 ? 8 : 0) // Simulate speed drop
  }));

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
            <div className="vessel-imo" style={{ opacity: 0.7 }}>IMO: {vessel.vessel_id}</div>
          </div>
        </div>
        <button className="close-btn" onClick={onClose}><X size={24} /></button>
      </div>

      <div className="dossier-grid">


        {/* Trajectory Analysis */}
        <div className="dossier-box full-width">
          <h3 className="box-title" style={{ display: 'flex', justifyContent: 'space-between' }}>
            TRAJECTORY ANALYSIS 
            {vessel.anomaly_score > 0.5 && <ShieldAlert size={14} className="icon-accent-red" />}
          </h3>
          <div style={{ height: '100px', width: '100%', marginTop: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={speedData}>
                <defs>
                  <linearGradient id="colorSpeed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0284c7" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#0284c7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="speed" stroke="#0284c7" fillOpacity={1} fill="url(#colorSpeed)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Anomaly Detection */}
        {vessel.anomaly_score > 0.5 && (
          <div className="dossier-box full-width alert-box">
            <h3 className="box-title" style={{ color: 'var(--accent-red)' }}>
              <Radio size={14} style={{ marginRight: '6px' }}/> ANOMALY DETECTION
            </h3>
            <p className="alert-text">
              **CRITICAL WARNING**<br/>
              Unreported discharge detected near {vessel.track[0][0].toFixed(2)}N, {vessel.track[0][1].toFixed(2)}E.<br/>
              Speed drop anomaly matches Fay spreading model timeline.
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}
