import { GameObjectData, CLASS_SPRITES, CLASS_NAMES } from "./types";

interface InventoryProps {
  objects: GameObjectData[];
  myNoid: number;
  selectedNoid: number | null;
  onSelect: (noid: number, classId: number) => void;
}

export default function Inventory({ objects, myNoid, selectedNoid, onSelect }: InventoryProps) {
  const carried = objects.filter(o => o.container_noid === myNoid);

  return (
    <div style={{
      background: "#0a0a14", border: "1px solid #333", borderRadius: 4,
      padding: 8,
    }}>
      <div style={{ color: "#666", fontSize: 11, marginBottom: 4, textAlign: "center" }}>
        Inventory ({carried.length})
      </div>
      {carried.length === 0 ? (
        <div style={{ color: "#444", fontSize: 11, textAlign: "center", padding: "8px 0" }}>
          Empty
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {carried.map(obj => {
            const sprite = CLASS_SPRITES[obj.class_id] || { char: "?", color: "#888" };
            const name = obj.extra?.name || CLASS_NAMES[obj.class_id] || "???";
            const isSelected = obj.noid === selectedNoid;
            return (
              <div
                key={obj.noid}
                onClick={() => onSelect(obj.noid, obj.class_id)}
                style={{
                  display: "flex", alignItems: "center", gap: 6,
                  padding: "3px 6px", borderRadius: 3, cursor: "pointer",
                  background: isSelected ? "#1a1a3a" : "transparent",
                  border: isSelected ? `1px solid ${sprite.color}` : "1px solid transparent",
                }}
              >
                <span style={{ color: sprite.color, fontFamily: "monospace", fontSize: 14, width: 16, textAlign: "center" }}>
                  {sprite.char}
                </span>
                <span style={{ color: isSelected ? sprite.color : "#aaa", fontSize: 11, fontFamily: "monospace" }}>
                  {name}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
