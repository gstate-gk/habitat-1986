import { RegionData } from "./types";

interface MiniMapProps {
  currentRegionId: number;
  onNavigate: (regionId: number) => void;
}

const ROOMS: { id: number; name: string; x: number; y: number; color: string }[] = [
  { id: 1, name: "Town Square", x: 145, y: 165, color: "#00ff88" },
  { id: 2, name: "Bank", x: 40, y: 165, color: "#ffcc00" },
  { id: 3, name: "Store", x: 250, y: 165, color: "#ff8844" },
  { id: 4, name: "Park", x: 145, y: 280, color: "#44cc44" },
  { id: 5, name: "Teleport", x: 250, y: 280, color: "#44ccff" },
  { id: 6, name: "Haunted", x: 40, y: 50, color: "#aa44ff" },
  { id: 7, name: "Lounge", x: 250, y: 50, color: "#ff44aa" },
];

const CONNECTIONS: [number, number][] = [
  [1, 2], [1, 3], [1, 4], [1, 6], [1, 7], [4, 5],
];

export default function MiniMap({ currentRegionId, onNavigate }: MiniMapProps) {
  return (
    <div style={{
      background: "#0a0a14", border: "1px solid #333", borderRadius: 4,
      padding: 8,
    }}>
      <div style={{ color: "#666", fontSize: 11, marginBottom: 4, textAlign: "center" }}>
        World Map
      </div>
      <svg width="100%" viewBox="0 0 290 330" style={{ display: "block" }}>
        {CONNECTIONS.map(([a, b]) => {
          const ra = ROOMS.find(r => r.id === a)!;
          const rb = ROOMS.find(r => r.id === b)!;
          return (
            <line key={`${a}-${b}`}
              x1={ra.x} y1={ra.y} x2={rb.x} y2={rb.y}
              stroke="#333" strokeWidth={1.5}
            />
          );
        })}
        {ROOMS.map(room => {
          const isCurrent = room.id === currentRegionId;
          return (
            <g key={room.id} onClick={() => onNavigate(room.id)} style={{ cursor: "pointer" }}>
              <rect
                x={room.x - 34} y={room.y - 14} width={68} height={28}
                rx={4} fill={isCurrent ? room.color + "33" : "#111"}
                stroke={isCurrent ? room.color : "#444"}
                strokeWidth={isCurrent ? 2.5 : 1}
              />
              <text
                x={room.x} y={room.y + 5}
                textAnchor="middle" fontSize={12}
                fill={isCurrent ? room.color : "#999"}
                fontFamily="monospace" fontWeight={isCurrent ? "bold" : "normal"}
              >
                {room.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
