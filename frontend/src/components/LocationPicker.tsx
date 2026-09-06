import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import L from "leaflet";

// Default Leaflet marker icons don't resolve correctly under bundlers unless reset like this.
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface Props {
  latitude: number | null;
  longitude: number | null;
  onChange: (lat: number, lng: number) => void;
}

function ClickHandler({ onChange }: { onChange: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onChange(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function LocationPicker({ latitude, longitude, onChange }: Props) {
  const center: [number, number] = [latitude ?? 20.5937, longitude ?? 78.9629];

  return (
    <div className="rounded-sm overflow-hidden border border-slate/15" style={{ height: 220 }}>
      <MapContainer center={center} zoom={latitude ? 13 : 4} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {latitude != null && longitude != null && <Marker position={[latitude, longitude]} />}
        <ClickHandler onChange={onChange} />
      </MapContainer>
    </div>
  );
}
