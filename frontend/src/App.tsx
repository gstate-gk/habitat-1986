import { useState, useCallback, useRef } from "react";
import { useWebSocket } from "./useWebSocket";
import GameCanvas from "./GameCanvas";
import ActionPanel from "./ActionPanel";
import StatusBar from "./StatusBar";
import ChatLog from "./ChatLog";
import LoginScreen from "./LoginScreen";
import MiniMap from "./MiniMap";
import Inventory from "./Inventory";
import CharacterInfo from "./CharacterInfo";
import HelpOverlay, { HelpButton } from "./HelpOverlay";
import {
  RegionData,
  GameObjectData,
  AvatarData,
  ChatMessage,
} from "./types";

export default function App() {
  const [playerName, setPlayerName] = useState<string | null>(null);
  const [region, setRegion] = useState<RegionData | null>(null);
  const [objects, setObjects] = useState<GameObjectData[]>([]);
  const [avatars, setAvatars] = useState<AvatarData[]>([]);
  const [myNoid, setMyNoid] = useState(0);
  const [myAvatar, setMyAvatar] = useState<AvatarData | null>(null);
  const [selectedNoid, setSelectedNoid] = useState<number | null>(null);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [showHelp, setShowHelp] = useState(true);

  const addChat = useCallback((name: string, text: string) => {
    setChatMessages((prev) => [...prev.slice(-99), { name, text, time: Date.now() }]);
  }, []);

  const addSystem = useCallback((text: string) => {
    addChat("System", text);
  }, [addChat]);

  const handleMessage = useCallback(
    (msg: any) => {
      switch (msg.type) {
        case "INIT":
        case "REGION_CHANGE": {
          setRegion(msg.region);
          setObjects(msg.objects || []);
          setAvatars(msg.avatars || []);
          setMyNoid(msg.your_noid);
          setMyAvatar(msg.avatar);
          setSelectedNoid(null);
          setSelectedClassId(null);
          if (msg.type === "INIT") {
            addSystem("ようこそ Habitat へ! 右上の [?] でガイドを表示できます");
            addSystem("ヒント: オブジェクトをクリック → アクションボタンで操作");
          }
          if (msg.type === "REGION_CHANGE") {
            addSystem(`Entered ${msg.region.name}`);
          }
          break;
        }
        case "AVATAR_ENTER": {
          setAvatars((prev) => {
            if (prev.find((a) => a.noid === msg.noid)) return prev;
            return [...prev, {
              noid: msg.noid, name: msg.name,
              x: msg.x, y: msg.y, health: 255, tokens: 0,
            }];
          });
          addSystem(`${msg.name} entered the region`);
          break;
        }
        case "AVATAR_LEAVE": {
          setAvatars((prev) => prev.filter((a) => a.noid !== msg.noid));
          addSystem(`${msg.name} left the region`);
          break;
        }
        case "WALK": {
          setAvatars((prev) =>
            prev.map((a) => a.noid === msg.noid ? { ...a, x: msg.x, y: msg.y } : a)
          );
          break;
        }
        case "SPEAK": {
          addChat(msg.name, msg.text);
          break;
        }
        case "POSTURE": {
          setAvatars((prev) =>
            prev.map((a) => a.noid === msg.noid ? { ...a, activity: msg.posture } : a)
          );
          break;
        }
        case "GRAB": {
          setObjects((prev) =>
            prev.map((o) => o.noid === msg.target ? { ...o, container_noid: msg.noid } : o)
          );
          break;
        }
        case "HAND": {
          setObjects((prev) =>
            prev.map((o) =>
              o.noid === msg.target ? { ...o, container_noid: 0, x: msg.x, y: msg.y } : o
            )
          );
          break;
        }
        case "DOOR_TOGGLE": {
          setObjects((prev) =>
            prev.map((o) => o.noid === msg.noid ? { ...o, gr_state: msg.open ? 1 : 0 } : o)
          );
          addSystem(`Door ${msg.open ? "opened" : "closed"}`);
          break;
        }
        case "GUN_SHOT": {
          addSystem("Shot fired!");
          setAvatars((prev) =>
            prev.map((a) =>
              a.noid === msg.target_noid ? { ...a, health: Math.max(0, a.health - msg.damage) } : a
            )
          );
          break;
        }
        case "AVATAR_DEATH": {
          addSystem(`${msg.name} has been defeated!`);
          break;
        }
        case "VENDO_PURCHASE": {
          addSystem(`${msg.buyer} bought ${msg.item}`);
          break;
        }
        case "ACTION_RESULT": {
          if (msg.error) {
            addSystem(`Error: ${msg.error}`);
          } else if (msg.type === "identify") {
            addSystem(`[${msg.class_name}] ${msg.name || ""}`);
          } else if (msg.type === "SIGN_READ" || msg.type === "PAPER_READ") {
            addSystem(`"${msg.text}"${msg.author ? ` — ${msg.author}` : ""}`);
          } else if (msg.type === "ATM_RESULT") {
            if (msg.action === "balance") {
              addSystem(`Bank: ${msg.balance} | Tokens: ${msg.tokens}`);
            } else {
              addSystem(
                `${msg.action === "deposit" ? "Deposited" : "Withdrew"} ${msg.amount}. ` +
                `Bank: ${msg.balance}, Tokens: ${msg.tokens}`
              );
            }
            setMyAvatar((prev) =>
              prev ? { ...prev, bank_account: msg.balance, tokens: msg.tokens } : prev
            );
          } else if (msg.type === "VENDO_DISPLAY") {
            addSystem(`Item: ${msg.item_name} — ${msg.item_price} tokens`);
          } else if (msg.type === "VENDO_BOUGHT") {
            addSystem(`Bought ${msg.item} for ${msg.price} tokens`);
            setMyAvatar((prev) => prev ? { ...prev, tokens: msg.tokens } : prev);
          } else if (msg.type === "MAIL_CHECK") {
            if (msg.count === 0) {
              addSystem("Mailbox is empty.");
            } else {
              addSystem(`You have ${msg.count} message(s).`);
              for (const m of msg.messages || []) {
                addChat(m.from, m.text);
              }
            }
          } else if (msg.type === "MAIL_RECEIVED") {
            addChat(msg.message.from, msg.message.text);
          } else if (msg.type === "TELEPORT_READY") {
            addSystem("Teleport booth activated! Press Teleport to go.");
          } else if (msg.type === "TOKENS_PICKED") {
            addSystem(`Picked up ${msg.amount} tokens (total: ${msg.total})`);
            setMyAvatar((prev) => prev ? { ...prev, tokens: msg.total } : prev);
          }
          break;
        }
      }
    },
    [addChat, addSystem]
  );

  const { connect, send, connected } = useWebSocket(playerName || "", handleMessage);

  const hasConnected = useRef(false);
  if (playerName && !hasConnected.current) {
    hasConnected.current = true;
    setTimeout(() => connect(), 50);
  }

  const handleAction = useCallback((msg: any) => send(msg), [send]);

  const handleClickObject = useCallback((noid: number, classId: number) => {
    setSelectedNoid(noid);
    setSelectedClassId(classId);
  }, []);

  const handleClickGround = useCallback(
    (x: number, y: number) => {
      setSelectedNoid(null);
      setSelectedClassId(null);
      send({ action: "WALK", noid: myNoid, args: { x, y } });
      setAvatars((prev) => prev.map((a) => (a.noid === myNoid ? { ...a, x, y } : a)));
    },
    [send, myNoid]
  );

  const handleNavigate = useCallback(
    (regionId: number) => {
      // Find a door that leads to the target region, or use direct navigation
      const door = objects.find(
        (o) => o.class_id === 23 && o.extra?.destination_region === regionId
      );
      if (door) {
        send({ action: "DO", noid: door.noid, args: {} });
      } else {
        // Use GOTO action for minimap navigation
        send({ action: "GOTO", args: { region_id: regionId } });
      }
    },
    [objects, send]
  );

  if (!playerName) {
    return <LoginScreen onLogin={setPlayerName} />;
  }

  return (
    <>
      {showHelp && <HelpOverlay onClose={() => setShowHelp(false)} />}
      <HelpButton onClick={() => setShowHelp(true)} />
      <div style={{
        display: "flex", flexDirection: "column", gap: 8,
        maxWidth: 960, margin: "0 auto", padding: 16,
        fontFamily: "monospace", background: "#050510", minHeight: "100vh",
      }}>
        <StatusBar avatar={myAvatar} regionName={region?.name || "..."} connected={connected} />
        <div style={{ display: "flex", gap: 8 }}>
          {/* Main column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1, minWidth: 0 }}>
            <GameCanvas
              region={region} objects={objects} avatars={avatars}
              myNoid={myNoid} selectedNoid={selectedNoid}
              onClickObject={handleClickObject} onClickGround={handleClickGround}
            />
            <ActionPanel
              selectedNoid={selectedNoid} selectedClassId={selectedClassId}
              myAvatar={myAvatar} objects={objects} onAction={handleAction}
            />
            <ChatLog messages={chatMessages} />
          </div>
          {/* Sidebar */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8, width: 290, flexShrink: 0 }}>
            <MiniMap currentRegionId={region?.id || 1} onNavigate={handleNavigate} />
            <CharacterInfo avatar={myAvatar} />
            <Inventory
              objects={objects} myNoid={myNoid}
              selectedNoid={selectedNoid} onSelect={handleClickObject}
            />
          </div>
        </div>
      </div>
    </>
  );
}
