export default function VesselRanking({ vessels, selectedVesselId, onSelectVessel }) {
  return (
    <div style={{ padding: '20px' }}>
      <h2>Suspect Vessels</h2>
      {vessels.map((vessel, index) => {
        const isTopSuspect = index === 0;
        const isSelected = vessel.vessel_id === selectedVesselId;

        return (
          <div 
            key={vessel.vessel_id} 
            onClick={() => onSelectVessel(vessel.vessel_id)}
            style={{
              padding: '15px',
              marginBottom: '10px',
              backgroundColor: isSelected ? '#e0f7fa' : '#fff',
              border: isTopSuspect ? '2px solid red' : '1px solid #ddd',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            <h3 style={{ margin: '0 0 10px 0' }}>
              {vessel.name} {isTopSuspect && "🚨 (Primary)"}
            </h3>
            <p style={{ margin: '5px 0' }}><strong>Overall Suspicion: {(vessel.score * 100).toFixed(0)}%</strong></p>
            <div style={{ fontSize: '0.9em', color: '#555' }}>
              <p style={{ margin: '2px 0' }}>Proximity: {(vessel.proximity_score * 100).toFixed(0)}%</p>
              <p style={{ margin: '2px 0' }}>Trajectory: {(vessel.trajectory_score * 100).toFixed(0)}%</p>
              <p style={{ margin: '2px 0' }}>Anomaly: {(vessel.anomaly_score * 100).toFixed(0)}%</p>
            </div>
          </div>
        );
      })}
    </div>
  );

}