import { AvatarData } from "./types";

interface CharacterInfoProps {
  avatar: AvatarData | null;
}

export default function CharacterInfo({ avatar }: CharacterInfoProps) {
  if (!avatar) return null;

  const hpRatio = avatar.health / 255;
  const hpColor = hpRatio > 0.5 ? "#00cc00" : hpRatio > 0.25 ? "#cccc00" : "#cc0000";

  const stats = [
    { label: "HP", value: `${avatar.health}/255`, color: hpColor },
    { label: "Tokens", value: String(avatar.tokens ?? 0), color: "#ffcc00" },
    { label: "Bank", value: String(avatar.bank_account ?? 0), color: "#44aaff" },
  ];

  return (
    <div style={{
      background: "#0a0a14", border: "1px solid #333", borderRadius: 4,
      padding: 8,
    }}>
      <div style={{ color: "#666", fontSize: 11, marginBottom: 4, textAlign: "center" }}>
        Character
      </div>
      <div style={{ color: "#00ff88", fontSize: 13, fontFamily: "monospace", textAlign: "center", marginBottom: 6 }}>
        @ {avatar.name}
      </div>
      {/* HP bar */}
      <div style={{ margin: "0 4px 6px", background: "#220000", borderRadius: 2, height: 6 }}>
        <div style={{
          width: `${hpRatio * 100}%`, height: "100%",
          background: hpColor, borderRadius: 2,
          transition: "width 0.3s",
        }} />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {stats.map(s => (
          <div key={s.label} style={{
            display: "flex", justifyContent: "space-between",
            padding: "1px 4px", fontFamily: "monospace", fontSize: 11,
          }}>
            <span style={{ color: "#666" }}>{s.label}</span>
            <span style={{ color: s.color }}>{s.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
