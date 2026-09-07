import { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Polygon, Polyline, Marker, useMap, Tooltip } from 'react-leaflet';
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

// Marker at the DETECTED spill location (from the satellite image itself)
const spillDetectedIcon = L.divIcon({
  className: 'custom-sonar-beacon-container',
  html: `
    <div class="sonar-beacon">
      <div class="sonar-wave wave1"></div>
      <div class="sonar-wave wave2"></div>
      <div class="sonar-core">
        <div class="sonar-dot"></div>
      </div>
      <div class="sonar-badge">SATELLITE DETECTION</div>
    </div>
  `,
  iconSize: [0, 0],
  iconAnchor: [0, 0]
});

// Marker at the RECONSTRUCTED origin (from drift hindcasting) — a
// distinct point from where the spill was actually detected.
const estimatedOriginIcon = L.divIcon({
  className: 'custom-origin-marker-container',
  html: `
    <div class="origin-marker">
      <div class="origin-dot"></div>
      <div class="origin-badge">ESTIMATED ORIGIN</div>
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
        paddingOptions = {
          paddingTopLeft: [50, 50],
          paddingBottomRight: [600, 50],
          duration: 1.5
        };
      }
    } else {
      points = [
        ...data.spill.polygon,
        [data.drift.estimated_origin.lat, data.drift.estimated_origin.lon],
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
  const estimatedOrigin = [data.drift.estimated_origin.lat, data.drift.estimated_origin.lon];

  return (
    <MapContainer center={spillCentroid} zoom={11} style={{ height: '100%', width: '100%', backgroundColor: '#050505' }} zoomControl={false}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        className="dark-map-tiles"
      />

      <FitBounds data={data} selectedVesselId={selectedVesselId} />

      {/* Detected spill location (satellite imagery) */}
      <Marker position={spillCentroid} icon={spillDetectedIcon} />

      {/* Reconstructed origin (drift hindcast) — a distinct point */}
      <Marker position={estimatedOrigin} icon={estimatedOriginIcon} />

      {/* Spill Polygon */}
      <Polygon positions={data.spill.polygon} pathOptions={{ color: 'var(--accent-red)', fillColor: '#1a110a', fillOpacity: 0.75, weight: 2 }} />

      {/* Hindcast Path (where it came from) */}
      <Polyline className="animated-path" positions={data.drift.hindcast_path.map(p => [p[0], p[1]])} pathOptions={{ color: 'var(--accent-blue)', dashArray: '5, 10', weight: 2 }} />
      {/* Invisible thick line for easy tooltip hover */}
      <Polyline positions={data.drift.hindcast_path.map(p => [p[0], p[1]])} pathOptions={{ color: 'transparent', weight: 20 }}>
        <Tooltip sticky className="dark-tooltip">Hindcast Path (Spill Origin Tracker)</Tooltip>
      </Polyline>

      {/* Forecast Path (where it is going) */}
      <Polyline className="animated-path" positions={data.drift.forecast_path.map(p => [p[0], p[1]])} pathOptions={{ color: 'var(--accent-purple)', dashArray: '5, 10', weight: 2 }} />
      {/* Invisible thick line for easy tooltip hover */}
      <Polyline positions={data.drift.forecast_path.map(p => [p[0], p[1]])} pathOptions={{ color: 'transparent', weight: 20 }}>
        <Tooltip sticky className="dark-tooltip">Forecast Path (Future Drift Prediction)</Tooltip>
      </Polyline>

      {/* Vessel Tracks */}
      {data.vessels.map((vessel) => {
        const isSelected = vessel.vessel_id === selectedVesselId;
        return [
          <Polyline
            key={`track-${vessel.vessel_id}`}
            positions={vessel.track.map(p => [p[0], p[1]])}
            pathOptions={{
              color: isSelected ? 'var(--accent-blue)' : 'rgba(255,255,255,0.2)',
              weight: isSelected ? 4 : 2,
              opacity: isSelected ? 1 : 0.6
            }}
          />,
          <Polyline
            key={`hover-${vessel.vessel_id}`}
            positions={vessel.track.map(p => [p[0], p[1]])}
            pathOptions={{ color: 'transparent', weight: 20 }}
          >
            <Tooltip sticky className="dark-tooltip">
              Vessel Track: {vessel.vessel_name || vessel.vessel_id}
            </Tooltip>
          </Polyline>
        ];
      })}
    </MapContainer>
  );
}