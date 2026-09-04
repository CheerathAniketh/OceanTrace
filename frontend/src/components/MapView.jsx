import { useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';

// Fits the map view to whatever data is actually on screen instead of a fixed zoom
function FitBounds({ data }) {
  const map = useMap();

  useEffect(() => {
    const points = [
      ...data.spill.polygon,
      ...data.drift.hindcast_path.map(p => [p[0], p[1]]),
      ...data.drift.forecast_path.map(p => [p[0], p[1]]),
      ...data.vessels.flatMap(v => v.track.map(p => [p[0], p[1]])),
    ];

    if (points.length > 0) {
      const bounds = L.latLngBounds(points);
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [data, map]);

  return null;
}

export default function MapView({ data, selectedVesselId }) {
  const center = data.spill.polygon[0];

  return (
    <MapContainer center={center} zoom={11} style={{ height: '100%', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />

      <FitBounds data={data} />

      {/* Spill Polygon */}
      <Polygon positions={data.spill.polygon} pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.4 }} />

      {/* Hindcast Path (where it came from) */}
      <Polyline positions={data.drift.hindcast_path.map(p => [p[0], p[1]])} pathOptions={{ color: 'purple', dashArray: '5, 10' }} />

      {/* Forecast Path (where it is going) */}
      <Polyline positions={data.drift.forecast_path.map(p => [p[0], p[1]])} pathOptions={{ color: 'orange', dashArray: '5, 10' }} />

      {/* Vessel Tracks */}
      {data.vessels.map((vessel) => {
        const isSelected = vessel.vessel_id === selectedVesselId;
        return (
          <Polyline
            key={vessel.vessel_id}
            positions={vessel.track.map(p => [p[0], p[1]])}
            pathOptions={{
              color: isSelected ? 'blue' : 'gray',
              weight: isSelected ? 5 : 2
            }}
          />
        );
      })}
    </MapContainer>
  );
}