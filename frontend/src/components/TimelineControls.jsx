import React, { useState } from 'react';
import { Play, Pause, SkipBack, SkipForward, Activity } from 'lucide-react';

export default function TimelineControls({ data }) {
  const [isPlaying, setIsPlaying] = useState(false);

  if (!data || !data.drift) return null;

  // We are just simulating the timeline for the demo look
  const togglePlay = () => setIsPlaying(!isPlaying);

  return (
    <div className="timeline-widget glass-panel">
      <div className="timeline-header">
        <Activity className="icon-accent-blue" size={16} />
        <span>DRIFT SIMULATION TIMELINE</span>
      </div>
      
      <div className="timeline-track-container">
        <span className="time-label">T-0</span>
        <div className="timeline-track">
          <div className="timeline-progress" style={{ width: '45%' }}></div>
          <div className="timeline-thumb" style={{ left: '45%' }}></div>
          
          {/* Markers */}
          <div className="timeline-marker" style={{ left: '25%' }}></div>
          <div className="timeline-marker" style={{ left: '50%' }}></div>
          <div className="timeline-marker" style={{ left: '75%' }}></div>
        </div>
        <span className="time-label">+48H</span>
      </div>

      <div className="timeline-controls">
        <button className="control-btn"><SkipBack size={16} /></button>
        <button className="control-btn play-btn" onClick={togglePlay}>
          {isPlaying ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
        </button>
        <button className="control-btn"><SkipForward size={16} /></button>
        
        <div className="current-time-display">
          SIMULATION ACTIVE <span className="blinking-dot"></span>
        </div>
      </div>
    </div>
  );
}
