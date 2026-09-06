import { useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Polyline, CircleMarker, useMap } from 'react-leaflet';
import L from 'leaflet';

// Fits the map view to whatever data is actually on screen instead of a fixed zoom
function FitBounds({ data, selectedVesselId }) {
  const map = useMap();

  useEffect(() => {
    let points = [];
    let paddingOptions = { padding: [40, 40] };

    if (selectedVesselId) {
      const vessel = data.vessels.find(v => v.vessel_id === selectedVesselId);
      if (vessel) {
        points = vessel.track.map(p => [p[0], p[1]]);
        // Shift map to the left so it isn't hidden under the DossierPanel
        paddingOptions = {
          paddingTopLeft: [50, 50],
          paddingBottomRight: [600, 50],
          duration: 1.5
        };
      }
    } else {
      points = [
        ...data.spill.polygon,
        ...data.drift.hindcast_path.map(p => [p[0], p[1]]),
        ...data.drift.forecast_path.map(p => [p[0], p[1]]),
        ...data.vessels.flatMap(v => v.track.map(p => [p[0], p[1]])),
      ];
      paddingOptions = { padding: [80, 80], duration: 1.5 };
    }

    if (points.length > 0) {
      const bounds = L.latLngBounds(points);
      map.flyToBounds(bounds, paddingOptions);
    }
  }, [data, selectedVesselId, map]);

  return null;
}

export default function MapView({ data, selectedVesselId }) {
  const center = data.spill.polygon[0];

  return (
    <MapContainer center={center} zoom={11} style={{ height: '100%', width: '100%', backgroundColor: '#050505' }} zoomControl={false}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        className="dark-map-tiles"
      />

      <FitBounds data={data} selectedVesselId={selectedVesselId} />

      {/* Radar Ping */}
      <CircleMarker 
        center={center} 
        radius={20} 
        pathOptions={{ stroke: false, className: 'radar-ping' }} 
      />

      {/* Spill Polygon */}
      <Polygon positions={data.spill.polygon} pathOptions={{ color: 'var(--accent-red)', fillColor: 'var(--accent-red)', fillOpacity: 0.15, weight: 2 }} />

      {/* Hindcast Path (where it came from) */}
      <Polyline className="animated-path" positions={data.drift.hindcast_path.map(p => [p[0], p[1]])} pathOptions={{ color: 'var(--accent-blue)', dashArray: '5, 10', weight: 2 }} />

      {/* Forecast Path (where it is going) */}
      <Polyline className="animated-path" positions={data.drift.forecast_path.map(p => [p[0], p[1]])} pathOptions={{ color: 'var(--accent-purple)', dashArray: '5, 10', weight: 2 }} />

      {/* Vessel Tracks */}
      {data.vessels.map((vessel) => {
        const isSelected = vessel.vessel_id === selectedVesselId;
        return (
          <Polyline
            key={vessel.vessel_id}
            positions={vessel.track.map(p => [p[0], p[1]])}
            pathOptions={{
              color: isSelected ? 'var(--accent-blue)' : 'rgba(255,255,255,0.2)',
              weight: isSelected ? 4 : 2,
              opacity: isSelected ? 1 : 0.6
            }}
          />
        );
      })}
    </MapContainer>
  );
}