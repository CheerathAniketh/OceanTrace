import { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Polygon, Polyline, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';

function getCentroid(polygon) {
  if (!polygon || polygon.length === 0) return [0, 0];
  let latSum = 0;
  let lngSum = 0;
  polygon.forEach(([lat, lng]) => {
    latSum += lat;
    lngSum += lng;
  });
  return [latSum / polygon.length, lngSum / polygon.length];
}

const sonarBeaconIcon = L.divIcon({
  className: 'custom-sonar-beacon-container',
  html: `
    <div class="sonar-beacon">
      <div class="sonar-wave wave1"></div>
      <div class="sonar-wave wave2"></div>
      <div class="sonar-core">
        <div class="sonar-dot"></div>
      </div>
      <div class="sonar-badge">SPILL ORIGIN</div>
    </div>
  `,
  iconSize: [0, 0],
  iconAnchor: [0, 0]
});

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
  const spillCentroid = useMemo(() => getCentroid(data.spill.polygon), [data.spill.polygon]);

  return (
    <MapContainer center={spillCentroid} zoom={11} style={{ height: '100%', width: '100%', backgroundColor: '#050505' }} zoomControl={false}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        className="dark-map-tiles"
      />

      <FitBounds data={data} selectedVesselId={selectedVesselId} />

      {/* Tactical Sonar Beacon at Spill Centroid */}
      <Marker position={spillCentroid} icon={sonarBeaconIcon} />

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