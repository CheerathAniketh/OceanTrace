import React from 'react';
import { Droplet, Clock, Map, AlertTriangle, AlertCircle } from 'lucide-react';

export default function SpillAnalytics({ data }) {
  if (!data || !data.spill) return null;

  const { area_km2, detected_at, estimated_age } = data.spill;

  // Format detection time
  const detectionDate = new Date(detected_at);
  const formattedDate = detectionDate.toLocaleString('en-US', { 
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' 
  });

  return (
    <div className="analytics-widget glass-panel">
      <div className="widget-header">
        <Droplet className="icon-accent-red" size={20} />
        <h2>SPILL INTELLIGENCE</h2>
      </div>

      <div className="metric-grid">
        <div className="metric-box">
          <div className="metric-title">
            <Map size={14} className="icon-muted" />
            <span>Estimated Area</span>
          </div>
          <div className="metric-value highlight-red">
            {area_km2.toFixed(2)} <span className="metric-unit">km²</span>
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-title">
            <Clock size={14} className="icon-muted" />
            <span>Detection Time</span>
          </div>
          <div className="metric-value text-small">
            {formattedDate}
          </div>
        </div>

        {estimated_age && (
          <div className="metric-box full-width">
            <div className="metric-title">
              <AlertTriangle size={14} className={estimated_age.regime_valid ? 'icon-accent-orange' : 'icon-muted'} />
              <span>Estimated Age (Fay Model)</span>
            </div>
            <div className="metric-value highlight-orange">
              {estimated_age.estimated_age_hours.toFixed(1)} <span className="metric-unit">hours</span>
            </div>
            {!estimated_age.regime_valid && (
              <div className="caveat-box">
                <AlertCircle size={12} />
                <span>Outside valid regime. Reliability low.</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
