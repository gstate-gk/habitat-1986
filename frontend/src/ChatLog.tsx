import { useRef, useEffect } from "react";
import { ChatMessage } from "./types";

interface ChatLogProps {
  messages: ChatMessage[];
  style?: React.CSSProperties;
}

export default function ChatLog({ messages, style }: ChatLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div style={{
      background: "#0a0a14", border: "1px solid #333",
      borderRadius: 4, minHeight: 100, overflowY: "auto",
      fontFamily: "monospace", fontSize: 12, ...style,
    }}>
      {/* Header */}
      <div style={{
        position: "sticky", top: 0, background: "#0a0a14",
        borderBottom: "1px solid #222", padding: "4px 10px",
        color: "#555", fontSize: 10, letterSpacing: 1,
      }}>
        CHAT LOG
      </div>
      <div style={{ padding: "4px 10px" }}>
        {messages.length === 0 && (
          <div style={{ color: "#333", fontSize: 11, padding: "12px 0", textAlign: "center" }}>
            — no messages —
          </div>
        )}
        {messages.map((m, i) => {
          const isSystem = m.name === "System";
          return (
            <div key={i} style={{
              padding: "2px 0",
              borderBottom: "1px solid #111",
            }}>
              <span style={{
                color: isSystem ? "#666" : "#00aaff",
                fontSize: 10,
              }}>
                {m.name}
              </span>
              <span style={{ color: "#333" }}> &gt; </span>
              <span style={{
                color: isSystem ? "#888" : "#ccc",
                fontSize: 12,
              }}>
                {m.text}
              </span>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
