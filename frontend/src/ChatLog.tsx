import { ChatMessage } from "./types";

interface ChatLogProps {
  messages: ChatMessage[];
}

export default function ChatLog({ messages }: ChatLogProps) {
  return (
    <div style={{
      background: "#0a0a14", border: "1px solid #333",
      borderRadius: 4, padding: 8, height: 150, overflowY: "auto",
      fontFamily: "monospace", fontSize: 13,
      display: "flex", flexDirection: "column-reverse",
    }}>
      <div>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 2 }}>
            <span style={{ color: "#00aaff" }}>{m.name}</span>
            <span style={{ color: "#666" }}> &gt; </span>
            <span style={{ color: "#ddd" }}>{m.text}</span>
          </div>
        ))}
        {messages.length === 0 && (
          <div style={{ color: "#444" }}>No messages yet. Say hello!</div>
        )}
      </div>
    </div>
  );
}
