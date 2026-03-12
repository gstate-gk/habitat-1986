import { useState } from "react";

interface LoginScreenProps {
  onLogin: (name: string) => void;
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [name, setName] = useState("");

  const handleSubmit = () => {
    const trimmed = name.trim();
    if (trimmed.length >= 1 && trimmed.length <= 20) {
      onLogin(trimmed);
    }
  };

  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      justifyContent: "center", height: "100vh", background: "#0a0a14",
      fontFamily: "monospace", color: "#ccc",
    }}>
      <div style={{
        border: "2px solid #333", borderRadius: 8, padding: 40,
        background: "#0c0c18", textAlign: "center", maxWidth: 500,
      }}>
        <h1 style={{ color: "#00ff88", fontSize: 36, marginBottom: 4 }}>HABITAT</h1>
        <div style={{ color: "#666", fontSize: 14, marginBottom: 24 }}>
          Lucasfilm Games &middot; 1986 &middot; The World's First MMO
        </div>

        <div style={{
          color: "#888", fontSize: 12, marginBottom: 24, lineHeight: 1.6,
          borderTop: "1px solid #222", borderBottom: "1px solid #222",
          padding: "16px 0",
        }}>
          Originally written in PL/I for Stratus VOS by Chip Morningstar.<br />
          Converted to Python + React as a legacy code research project.<br />
          <span style={{ color: "#555" }}>
            PL/I 26,218 lines → Python + React ~3,500 lines (87% reduction)
          </span>
        </div>

        <div style={{ marginBottom: 16, fontSize: 14, color: "#aaa" }}>
          Choose your avatar name:
        </div>

        <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="Enter name..."
            maxLength={20}
            style={{
              background: "#1a1a2e", color: "#00ff88", border: "1px solid #444",
              padding: "8px 14px", borderRadius: 4, fontFamily: "monospace",
              fontSize: 16, width: 200, textAlign: "center",
            }}
            autoFocus
          />
          <button
            onClick={handleSubmit}
            style={{
              background: "#1a3a1a", color: "#00ff88", border: "1px solid #0c0",
              padding: "8px 20px", borderRadius: 4, fontFamily: "monospace",
              fontSize: 16, cursor: "pointer",
            }}
          >
            Enter World
          </button>
        </div>

        <div style={{ marginTop: 24, color: "#444", fontSize: 11 }}>
          MIT License &middot; Copyright (c) 1985 Lucasfilm Games Division
        </div>
      </div>
    </div>
  );
}
