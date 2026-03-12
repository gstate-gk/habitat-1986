import React, { useState } from "react";
import { ClassID, CLASS_NAMES, GameObjectData, AvatarData } from "./types";

interface ActionPanelProps {
  selectedNoid: number | null;
  selectedClassId: number | null;
  myAvatar: AvatarData | null;
  objects: GameObjectData[];
  onAction: (msg: any) => void;
}

export default function ActionPanel({
  selectedNoid,
  selectedClassId,
  myAvatar,
  objects,
  onAction,
}: ActionPanelProps) {
  const [chatText, setChatText] = useState("");
  const [atmAmount, setAtmAmount] = useState(100);

  const selectedObj = objects.find((o) => o.noid === selectedNoid);
  const className = selectedClassId !== null ? (CLASS_NAMES[selectedClassId] || "Object") : "";

  const handleChat = () => {
    if (!chatText.trim() || !myAvatar) return;
    onAction({ action: "SPEAK", noid: myAvatar.noid, args: { text: chatText } });
    setChatText("");
  };

  // Context-sensitive action buttons
  const renderActions = () => {
    if (selectedNoid === null || selectedClassId === null) {
      return <div style={{ color: "#444", fontSize: 12 }}>オブジェクトをクリックして操作 / Click an object</div>;
    }

    const actions: React.ReactElement[] = [];

    // Common actions
    actions.push(
      <button key="help" onClick={() => onAction({ action: "HELP", noid: selectedNoid })}>
        Identify
      </button>
    );

    switch (selectedClassId) {
      case ClassID.DOOR:
        actions.push(
          <button key="go" onClick={() => onAction({ action: "GO", noid: selectedNoid, args: {} })}>
            Go Through
          </button>,
          <button key="do" onClick={() => onAction({ action: "DO", noid: selectedNoid })}>
            Open/Close
          </button>
        );
        break;
      case ClassID.TELEPORT:
        actions.push(
          <button key="pay" onClick={() => onAction({ action: "PAY", noid: selectedNoid, args: {} })}>
            Pay (10 tokens)
          </button>,
          <button key="do" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
            Teleport!
          </button>
        );
        break;
      case ClassID.ATM:
        actions.push(
          <button key="bal" onClick={() =>
            onAction({ action: "DO", noid: selectedNoid, args: { atm_action: "balance" } })
          }>
            Balance
          </button>,
          <span key="amt" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
            <input
              type="number" value={atmAmount} min={1}
              onChange={(e) => setAtmAmount(Number(e.target.value))}
              style={{ width: 60, background: "#1a1a2e", color: "#fff", border: "1px solid #444", padding: 2 }}
            />
            <button onClick={() =>
              onAction({ action: "DO", noid: selectedNoid, args: { atm_action: "deposit", amount: atmAmount } })
            }>
              Deposit
            </button>
            <button onClick={() =>
              onAction({ action: "DO", noid: selectedNoid, args: { atm_action: "withdraw", amount: atmAmount } })
            }>
              Withdraw
            </button>
          </span>
        );
        break;
      case ClassID.VENDO_FRONT:
        actions.push(
          <button key="next" onClick={() => onAction({ action: "DO", noid: selectedNoid })}>
            Next Item
          </button>,
          <button key="buy" onClick={() => onAction({ action: "PAY", noid: selectedNoid, args: {} })}>
            Buy
          </button>
        );
        break;
      case ClassID.SIGN:
      case ClassID.PAPER:
        actions.push(
          <button key="read" onClick={() => onAction({ action: "DO", noid: selectedNoid })}>
            Read
          </button>
        );
        break;
      case ClassID.MAILBOX:
        actions.push(
          <button key="check" onClick={() => onAction({ action: "DO", noid: selectedNoid })}>
            Check Mail
          </button>,
          <button key="get" onClick={() => onAction({ action: "GRAB", noid: selectedNoid, args: {} })}>
            Get Mail
          </button>
        );
        break;
      case ClassID.GUN:
      case ClassID.TOKENS:
      case ClassID.KEY:
      case ClassID.BAG:
        actions.push(
          <button key="grab" onClick={() => onAction({ action: "GRAB", noid: selectedNoid, args: {} })}>
            Pick Up
          </button>
        );
        if (selectedClassId === ClassID.GUN) {
          actions.push(
            <button key="shoot" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
              Shoot
            </button>
          );
        }
        break;
      // Weapons (melee/thrown)
      case ClassID.KNIFE:
      case ClassID.CLUB:
      case ClassID.BOOMERANG:
      case ClassID.STUN_GUN:
      case ClassID.FAKE_GUN:
      case ClassID.GRENADE:
        actions.push(
          <button key="grab" onClick={() => onAction({ action: "GRAB", noid: selectedNoid, args: {} })}>
            Pick Up
          </button>,
          <button key="attack" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
            Attack
          </button>
        );
        break;
      // Magic items
      case ClassID.AMULET:
      case ClassID.RING:
      case ClassID.CRYSTAL_BALL:
      case ClassID.MAGIC_LAMP:
      case ClassID.MAGIC_STAFF:
      case ClassID.MAGIC_WAND:
      case ClassID.GEMSTONE:
        actions.push(
          <button key="grab" onClick={() => onAction({ action: "GRAB", noid: selectedNoid, args: {} })}>
            Pick Up
          </button>,
          <button key="use" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
            Use Magic
          </button>
        );
        break;
      // Containers
      case ClassID.BOX:
      case ClassID.CHEST:
      case ClassID.SAFE:
      case ClassID.DISPLAY_CASE:
      case ClassID.GARBAGE_CAN:
      case ClassID.DROPBOX:
        actions.push(
          <button key="open" onClick={() => onAction({ action: "DO", noid: selectedNoid })}>
            Open/Close
          </button>,
          <button key="grab" onClick={() => onAction({ action: "GRAB", noid: selectedNoid, args: {} })}>
            Pick Up
          </button>
        );
        break;
      // Wearable
      case ClassID.HAT:
      case ClassID.JACKET:
      case ClassID.SHIRT:
      case ClassID.PANTS:
        actions.push(
          <button key="grab" onClick={() => onAction({ action: "GRAB", noid: selectedNoid, args: {} })}>
            Pick Up
          </button>,
          <button key="wear" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
            Wear/Remove
          </button>
        );
        break;
      // Machines
      case ClassID.COKE_MACHINE:
      case ClassID.FORTUNE_MACHINE:
      case ClassID.PAWN_MACHINE:
      case ClassID.CHANGOMATIC:
      case ClassID.SWITCH:
        actions.push(
          <button key="use" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
            Use
          </button>
        );
        break;
      // Creatures
      case ClassID.GHOST:
      case ClassID.HOUSE_CAT:
      case ClassID.BUREAUCRAT:
        actions.push(
          <button key="talk" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
            Interact
          </button>
        );
        if (selectedClassId === ClassID.HOUSE_CAT) {
          actions.push(
            <button key="grab" onClick={() => onAction({ action: "GRAB", noid: selectedNoid, args: {} })}>
              Pick Up
            </button>
          );
        }
        break;
      // Readable (book, plaque, short_sign)
      case ClassID.BOOK:
      case ClassID.PLAQUE:
      case ClassID.SHORT_SIGN:
        actions.push(
          <button key="read" onClick={() => onAction({ action: "DO", noid: selectedNoid })}>
            Read
          </button>
        );
        if (selectedClassId === ClassID.BOOK) {
          actions.push(
            <button key="grab" onClick={() => onAction({ action: "GRAB", noid: selectedNoid, args: {} })}>
              Pick Up
            </button>
          );
        }
        break;
      // Special
      case ClassID.HAND_OF_GOD:
      case ClassID.SEX_CHANGER:
        actions.push(
          <button key="use" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
            Use
          </button>
        );
        break;
      // Portable items (general)
      case ClassID.FLASHLIGHT:
      case ClassID.SHOVEL:
      case ClassID.COMPASS:
      case ClassID.TAPE:
      case ClassID.GLUE:
      case ClassID.SPRAY_CAN:
      case ClassID.MATCHBOOK:
      case ClassID.BOTTLE:
      case ClassID.DRUGS:
      case ClassID.SKATEBOARD:
      case ClassID.FRISBEE:
      case ClassID.BALL:
      case ClassID.WINDUP_TOY:
      case ClassID.MOVIE_CAMERA:
      case ClassID.TICKET:
      case ClassID.GAME_PIECE:
      case ClassID.DIE:
      case ClassID.HEAD:
        actions.push(
          <button key="grab" onClick={() => onAction({ action: "GRAB", noid: selectedNoid, args: {} })}>
            Pick Up
          </button>,
          <button key="use" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
            Use
          </button>
        );
        break;
      // Interactive furniture/scenery
      case ClassID.JUKEBOX:
      case ClassID.FOUNTAIN:
      case ClassID.HOT_TUB:
      case ClassID.ELEVATOR:
        actions.push(
          <button key="use" onClick={() => onAction({ action: "DO", noid: selectedNoid, args: {} })}>
            Use
          </button>
        );
        break;
      case ClassID.AVATAR:
        if (selectedNoid !== myAvatar?.noid) {
          actions.push(
            <span key="other" style={{ color: "#88aaff" }}>
              Another player
            </span>
          );
        }
        break;
    }

    return (
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
        <span style={{
          color: "#00ff88", fontSize: 11, background: "#0a2a0a",
          border: "1px solid #1a3a1a", borderRadius: 3,
          padding: "2px 8px", marginRight: 4,
        }}>
          {className}
        </span>
        {actions}
      </div>
    );
  };

  return (
    <div style={{
      background: "#0a0a14", border: "1px solid #333",
      borderRadius: 4, overflow: "hidden",
    }}>
      {/* Action buttons */}
      <div style={{
        padding: "8px 10px", minHeight: 36,
        borderBottom: "1px solid #222",
        display: "flex", alignItems: "center",
      }}>
        {renderActions()}
      </div>

      {/* Chat input */}
      <div style={{
        display: "flex", gap: 0,
        background: "#0c0c18",
      }}>
        <div style={{
          color: "#444", fontSize: 10, padding: "10px 8px 10px 10px",
          display: "flex", alignItems: "center", letterSpacing: 1,
        }}>
          SAY
        </div>
        <input
          type="text"
          value={chatText}
          onChange={(e) => setChatText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleChat()}
          placeholder="Type a message..."
          style={{
            flex: 1, background: "transparent", color: "#ddd",
            border: "none", padding: "8px 6px", outline: "none",
            fontFamily: "monospace", fontSize: 13,
          }}
        />
        <button
          onClick={handleChat}
          style={{
            background: "#1a1a3a", color: "#00ff88", border: "none",
            borderLeft: "1px solid #222",
            padding: "8px 16px", cursor: "pointer",
            fontFamily: "monospace", fontSize: 12, fontWeight: "bold",
            letterSpacing: 1,
          }}
        >
          SEND
        </button>
      </div>
    </div>
  );
}
