import { useState } from "react";

interface HelpOverlayProps {
  onClose: () => void;
}

const TIPS = [
  {
    title: "移動する",
    icon: "🖱️",
    desc: "地面をクリックするとアバターが歩きます",
  },
  {
    title: "オブジェクトを操作",
    icon: "👆",
    desc: "画面上のシンボル（+＝ドア、$＝ATM 等）をクリック → 下にアクションボタンが出ます",
  },
  {
    title: "部屋を移動",
    icon: "🚪",
    desc: "ドア（+）をクリック →「Go Through」で別の部屋へ。右のミニマップからも直接移動できます",
  },
  {
    title: "アイテムを拾う",
    icon: "🎒",
    desc: "アイテムをクリック →「Pick Up」で所持品に。右の Inventory に表示されます",
  },
  {
    title: "お金を使う",
    icon: "💰",
    desc: "ATM（$）で預金・引出し。自販機（V）でアイテム購入。トークンを拾って資金を得ましょう",
  },
  {
    title: "チャット",
    icon: "💬",
    desc: "画面下の入力欄にテキストを入れて Speak。他のプレイヤーと会話できます",
  },
  {
    title: "探索しよう",
    icon: "🗺️",
    desc: "7つの部屋があります: 広場・銀行・商店・公園・テレポート・幽霊屋敷・ラウンジ",
  },
];

export default function HelpOverlay({ onClose }: HelpOverlayProps) {
  const [page, setPage] = useState(0);
  const tip = TIPS[page];
  const isLast = page === TIPS.length - 1;

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0,
        background: "rgba(0,0,0,0.85)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#0c0c1a", border: "2px solid #444",
          borderRadius: 8, padding: 24, maxWidth: 400, width: "90%",
          fontFamily: "monospace", color: "#ccc",
        }}
      >
        {/* Header */}
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: 16,
        }}>
          <span style={{ color: "#00ff88", fontSize: 14 }}>
            Habitat ガイド ({page + 1}/{TIPS.length})
          </span>
          <button
            onClick={onClose}
            style={{
              background: "none", border: "1px solid #555", color: "#888",
              borderRadius: 4, padding: "2px 8px", cursor: "pointer", fontSize: 12,
            }}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div style={{ textAlign: "center", marginBottom: 20 }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>{tip.icon}</div>
          <div style={{ color: "#fff", fontSize: 16, marginBottom: 8 }}>{tip.title}</div>
          <div style={{ color: "#aaa", fontSize: 13, lineHeight: 1.6 }}>{tip.desc}</div>
        </div>

        {/* Navigation */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            style={{
              background: "#1a1a2e", border: "1px solid #444", color: page === 0 ? "#333" : "#aaa",
              borderRadius: 4, padding: "6px 16px", cursor: page === 0 ? "default" : "pointer",
              fontFamily: "monospace", fontSize: 12,
            }}
          >
            ← 前
          </button>

          {/* Dots */}
          <div style={{ display: "flex", gap: 4 }}>
            {TIPS.map((_, i) => (
              <div
                key={i}
                onClick={() => setPage(i)}
                style={{
                  width: 8, height: 8, borderRadius: "50%", cursor: "pointer",
                  background: i === page ? "#00ff88" : "#333",
                }}
              />
            ))}
          </div>

          <button
            onClick={() => isLast ? onClose() : setPage(p => p + 1)}
            style={{
              background: isLast ? "#00ff88" : "#1a1a2e",
              border: `1px solid ${isLast ? "#00ff88" : "#444"}`,
              color: isLast ? "#000" : "#aaa",
              borderRadius: 4, padding: "6px 16px", cursor: "pointer",
              fontFamily: "monospace", fontSize: 12, fontWeight: isLast ? "bold" : "normal",
            }}
          >
            {isLast ? "はじめる!" : "次 →"}
          </button>
        </div>
      </div>
    </div>
  );
}

/** Floating help button (always visible) */
export function HelpButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      title="遊び方ガイド"
      style={{
        position: "fixed", top: 12, right: 12, zIndex: 999,
        width: 36, height: 36, borderRadius: "50%",
        background: "#1a1a2e", border: "2px solid #00ff88",
        color: "#00ff88", fontSize: 18, fontWeight: "bold",
        cursor: "pointer", fontFamily: "monospace",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}
    >
      ?
    </button>
  );
}
