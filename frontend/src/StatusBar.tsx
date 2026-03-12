import { AvatarData } from "./types";

interface StatusBarProps {
  avatar: AvatarData | null;
  regionName: string;
  connected: boolean;
}

export default function StatusBar({ avatar, regionName, connected }: StatusBarProps) {
  if (!avatar) return null;

  const hpPct = Math.round((avatar.health / 255) * 100);
  const hpColor = hpPct > 50 ? "#0c0" : hpPct > 25 ? "#cc0" : "#c00";

  return (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      background: "#0a0a14", border: "1px solid #333",
      padding: "6px 12px", borderRadius: 4, fontFamily: "monospace", fontSize: 13,
    }}>
      <div style={{ display: "flex", gap: 16 }}>
        <span style={{ color: "#00ff88" }}>@{avatar.name}</span>
        <span style={{ color: hpColor }}>HP: {avatar.health}/255</span>
        <span style={{ color: "#ffff00" }}>Tokens: {avatar.tokens}</span>
        {avatar.bank_account !== undefined && (
          <span style={{ color: "#88aaff" }}>Bank: {avatar.bank_account}</span>
        )}
      </div>
      <div style={{ display: "flex", gap: 12 }}>
        <span style={{ color: "#aaa" }}>{regionName}</span>
        <span style={{ color: connected ? "#0c0" : "#c00" }}>
          {connected ? "ONLINE" : "OFFLINE"}
        </span>
      </div>
    </div>
  );
}
