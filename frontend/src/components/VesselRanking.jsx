import React, { useState } from 'react';
import { Target, Activity, ShieldAlert, Navigation } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } }
};

function trackedHours(track) {
  const start = new Date(track[0][2]);
  const end = new Date(track[track.length - 1][2]);
  return Math.max(0, Math.round((end - start) / 3600000));
}

export default function VesselRanking({ vessels, selectedVesselId, onSelectVessel }) {
  const [showAll, setShowAll] = useState(false);

  if (!vessels || vessels.length === 0) return null;

  const displayVessels = showAll ? vessels : vessels.slice(0, 5);

  return (
    <motion.div 
      className="vessel-list"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      <div className="vessel-header" style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Target className="icon-accent-blue" size={18} />
        <h2 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-primary)' }}>Suspect Vessels</h2>
      </div>
      
      {displayVessels.map((vessel) => {
        const isSelected = selectedVesselId === vessel.vessel_id;
        const totalScore = (vessel.score * 100).toFixed(0);

        // Chart now represents the SAME overall score shown as the
        // headline number, not just anomaly_score, so the two match.
        const chartData = [
          { name: 'Suspicion', value: vessel.score * 100 },
          { name: 'Remaining', value: 100 - (vessel.score * 100) }
        ];
        
        return (
          <motion.div 
            key={vessel.vessel_id} 
            layoutId={`vessel-${vessel.vessel_id}`}
            variants={cardVariants}
            className={`vessel-card ${isSelected ? 'selected' : ''}`}
            onClick={() => onSelectVessel(vessel.vessel_id)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="vessel-header" style={{ marginBottom: '8px' }}>
              <div className="vessel-title">
                <Navigation size={16} className={isSelected ? 'icon-accent-blue' : 'icon-muted'} />
                <span className="vessel-name">{vessel.name}</span>
              </div>
              <div className={`vessel-score ${totalScore > 75 ? 'high-risk' : 'med-risk'}`}>
                {totalScore}%
              </div>
            </div>
            
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              Vessel ID: {vessel.vessel_id}
            </div>

            <div className="vessel-stats-container" style={{ flexDirection: 'row', alignItems: 'center' }}>
              <div style={{ width: '60px', height: '60px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={20}
                      outerRadius={28}
                      startAngle={90}
                      endAngle={-270}
                      dataKey="value"
                      stroke="none"
                    >
                      <Cell fill={chartData[0].value > 50 ? 'var(--accent-red)' : 'var(--accent-blue)'} />
                      <Cell fill="#e2e8f0" />
                    </Pie>
                    <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                <div className="vessel-indicators">
                  <div className="indicator">
                    <Activity size={12} className="icon-muted" />
                    <span>{trackedHours(vessel.track)}h tracked</span>
                  </div>
                  {vessel.anomaly_score > 0.5 && (
                    <div className="indicator warning">
                      <ShieldAlert size={12} />
                      <span>Anomalous</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        );
      })}

      {vessels.length > 5 && (
        <button 
          className="show-more-btn"
          onClick={() => setShowAll(!showAll)}
        >
          {showAll ? 'Show Top 5 Only' : `Load Remaining (${vessels.length - 5})`}
        </button>
      )}
    </motion.div>
  );
}