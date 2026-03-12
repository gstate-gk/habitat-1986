import { useRef, useEffect, useCallback } from "react";
import {
  RegionData,
  GameObjectData,
  AvatarData,
  ClassID,
  CLASS_SPRITES,
  CLASS_NAMES,
} from "./types";

interface GameCanvasProps {
  region: RegionData | null;
  objects: GameObjectData[];
  avatars: AvatarData[];
  myNoid: number;
  selectedNoid: number | null;
  onClickObject: (noid: number, classId: number) => void;
  onClickGround: (x: number, y: number) => void;
}

const CANVAS_W = 640;
const CANVAS_H = 400;
const FONT = "16px monospace";
const FONT_LARGE = "20px monospace";
const FONT_SMALL = "11px monospace";

// Per-region color themes
const REGION_THEMES: Record<number, {
  sky: [string, string]; ground: [string, string];
  indoor: string; tile: string; wall: string;
}> = {
  1: { sky: ["#1a0a30", "#2a1555"], ground: ["#1a3a1a", "#0a200a"], indoor: "#0c0c18", tile: "#1a1a2e", wall: "#2a1a3a" }, // Town Square - default
  2: { sky: ["#1a1a00", "#2a2510"], ground: ["#2a2a0a", "#1a1a00"], indoor: "#12100a", tile: "#2a2818", wall: "#3a3020" }, // Bank - gold
  3: { sky: ["#0a1a30", "#152a55"], ground: ["#1a2a3a", "#0a1a2a"], indoor: "#0a0c18", tile: "#181a2e", wall: "#1a2a3a" }, // Store - blue
  4: { sky: ["#0a2010", "#153518"], ground: ["#0a3a0a", "#052005"], indoor: "#0a140a", tile: "#1a2e1a", wall: "#1a3a1a" }, // Park - green
  5: { sky: ["#200a30", "#351555"], ground: ["#2a1a3a", "#1a0a2a"], indoor: "#100a18", tile: "#2a1a2e", wall: "#3a1a3a" }, // Teleport - purple
  6: { sky: ["#0a0010", "#150020"], ground: ["#0a0a0a", "#050505"], indoor: "#06040a", tile: "#12101a", wall: "#1a0a2a" }, // Haunted - dark purple
  7: { sky: ["#200a0a", "#351515"], ground: ["#2a1010", "#1a0808"], indoor: "#140a0a", tile: "#2e1a1a", wall: "#3a1a2a" }, // Lounge - red/pink
};

// Convert world coordinates to canvas coordinates
function worldToCanvas(
  wx: number,
  wy: number,
  region: RegionData
): [number, number] {
  const sx = (wx / region.x_size) * CANVAS_W;
  const sy = CANVAS_H - (wy / region.y_size) * CANVAS_H;
  return [sx, sy];
}

function canvasToWorld(
  cx: number,
  cy: number,
  region: RegionData
): [number, number] {
  const wx = Math.round((cx / CANVAS_W) * region.x_size);
  const wy = Math.round(((CANVAS_H - cy) / CANVAS_H) * region.y_size);
  return [wx, wy];
}

export default function GameCanvas({
  region,
  objects,
  avatars,
  myNoid,
  selectedNoid,
  onClickObject,
  onClickGround,
}: GameCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrame = useRef<number>(0);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !region) return;
    const ctx = canvas.getContext("2d")!;

    // --- Background (per-region theme) ---
    const theme = REGION_THEMES[region.id] || REGION_THEMES[1];
    const isOutdoor = region.terrain_type === 1;
    if (isOutdoor) {
      // Sky gradient
      const skyGrad = ctx.createLinearGradient(0, 0, 0, CANVAS_H * 0.4);
      skyGrad.addColorStop(0, theme.sky[0]);
      skyGrad.addColorStop(1, theme.sky[1]);
      ctx.fillStyle = skyGrad;
      ctx.fillRect(0, 0, CANVAS_W, CANVAS_H * 0.4);

      // Stars
      ctx.fillStyle = "#ffffff";
      for (let i = 0; i < 30; i++) {
        const sx = ((i * 73 + 17) % CANVAS_W);
        const sy = ((i * 37 + 11) % (CANVAS_H * 0.35));
        ctx.fillRect(sx, sy, 1, 1);
      }

      // Ground
      const groundGrad = ctx.createLinearGradient(0, CANVAS_H * 0.4, 0, CANVAS_H);
      groundGrad.addColorStop(0, theme.ground[0]);
      groundGrad.addColorStop(1, theme.ground[1]);
      ctx.fillStyle = groundGrad;
      ctx.fillRect(0, CANVAS_H * 0.4, CANVAS_W, CANVAS_H * 0.6);
    } else {
      // Indoor — dark tiled floor
      ctx.fillStyle = theme.indoor;
      ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

      // Floor tiles
      ctx.strokeStyle = theme.tile;
      ctx.lineWidth = 0.5;
      for (let x = 0; x < CANVAS_W; x += 32) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, CANVAS_H);
        ctx.stroke();
      }
      for (let y = 0; y < CANVAS_H; y += 32) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(CANVAS_W, y);
        ctx.stroke();
      }

      // Walls
      ctx.fillStyle = theme.wall;
      ctx.fillRect(0, 0, CANVAS_W, 40);
      ctx.fillRect(0, 0, 8, CANVAS_H);
      ctx.fillRect(CANVAS_W - 8, 0, 8, CANVAS_H);
    }

    // --- Region name ---
    ctx.font = FONT_SMALL;
    ctx.fillStyle = "#888888";
    ctx.textAlign = "left";
    ctx.fillText(region.name, 12, 20);

    // --- Objects ---
    for (const obj of objects) {
      if (obj.container_noid !== 0) continue; // Only draw objects on the ground
      const [sx, sy] = worldToCanvas(obj.x, obj.y, region);
      const sprite = CLASS_SPRITES[obj.class_id] || { char: "?", color: "#888" };
      const isSelected = obj.noid === selectedNoid;

      // Selection highlight
      if (isSelected) {
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.strokeRect(sx - 14, sy - 16, 28, 24);
      }

      // Object glow
      ctx.shadowColor = sprite.color;
      ctx.shadowBlur = isSelected ? 12 : 4;

      // Draw character
      ctx.font = FONT_LARGE;
      ctx.fillStyle = sprite.color;
      ctx.textAlign = "center";
      ctx.fillText(sprite.char, sx, sy);

      ctx.shadowBlur = 0;

      // Label for doors, signs, teleports, ATM, vendo
      if ([ClassID.DOOR, ClassID.SIGN, ClassID.TELEPORT, ClassID.ATM,
           ClassID.VENDO_FRONT, ClassID.MAILBOX].includes(obj.class_id as any)) {
        ctx.font = FONT_SMALL;
        ctx.fillStyle = "#aaaaaa";
        const label = obj.extra?.text?.substring(0, 20) ||
                      CLASS_NAMES[obj.class_id] || "";
        ctx.fillText(label, sx, sy + 16);
      }
    }

    // --- Avatars ---
    for (const av of avatars) {
      const [sx, sy] = worldToCanvas(av.x, av.y, region);
      const isMe = av.noid === myNoid;
      const isSelected = av.noid === selectedNoid;

      // Selection ring
      if (isSelected) {
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.strokeRect(sx - 14, sy - 20, 28, 32);
      }

      // Avatar body
      ctx.shadowColor = isMe ? "#00ff88" : "#00aaff";
      ctx.shadowBlur = isMe ? 8 : 4;

      ctx.font = FONT_LARGE;
      ctx.fillStyle = isMe ? "#00ff88" : "#00aaff";
      ctx.textAlign = "center";
      ctx.fillText("@", sx, sy);
      ctx.shadowBlur = 0;

      // Name plate
      ctx.font = FONT_SMALL;
      ctx.fillStyle = isMe ? "#88ffaa" : "#88aaff";
      ctx.fillText(av.name, sx, sy - 16);

      // Health bar
      const barW = 30;
      const hpRatio = av.health / 255;
      ctx.fillStyle = "#330000";
      ctx.fillRect(sx - barW / 2, sy + 6, barW, 3);
      ctx.fillStyle = hpRatio > 0.5 ? "#00cc00" : hpRatio > 0.25 ? "#cccc00" : "#cc0000";
      ctx.fillRect(sx - barW / 2, sy + 6, barW * hpRatio, 3);
    }

    // --- Exit indicators (neighbors) ---
    ctx.font = FONT_SMALL;
    ctx.fillStyle = "#555555";
    ctx.textAlign = "center";
    if (region.neighbors.west) ctx.fillText("<< West", 40, CANVAS_H / 2);
    if (region.neighbors.east) ctx.fillText("East >>", CANVAS_W - 40, CANVAS_H / 2);
    if (region.neighbors.north) ctx.fillText("^ North", CANVAS_W / 2, 35);
    if (region.neighbors.south) ctx.fillText("v South", CANVAS_W / 2, CANVAS_H - 10);

    animFrame.current = requestAnimationFrame(draw);
  }, [region, objects, avatars, myNoid, selectedNoid]);

  useEffect(() => {
    animFrame.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animFrame.current);
  }, [draw]);

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!region) return;
      const rect = canvasRef.current!.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;

      // Check if clicked on an object or avatar
      for (const av of avatars) {
        const [sx, sy] = worldToCanvas(av.x, av.y, region);
        if (Math.abs(cx - sx) < 16 && Math.abs(cy - sy) < 16) {
          onClickObject(av.noid, ClassID.AVATAR);
          return;
        }
      }
      for (const obj of objects) {
        if (obj.container_noid !== 0) continue;
        const [sx, sy] = worldToCanvas(obj.x, obj.y, region);
        if (Math.abs(cx - sx) < 16 && Math.abs(cy - sy) < 16) {
          onClickObject(obj.noid, obj.class_id);
          return;
        }
      }

      // Clicked on empty ground — walk there
      const [wx, wy] = canvasToWorld(cx, cy, region);
      onClickGround(wx, wy);
    },
    [region, objects, avatars, onClickObject, onClickGround]
  );

  return (
    <canvas
      ref={canvasRef}
      width={CANVAS_W}
      height={CANVAS_H}
      onClick={handleClick}
      style={{
        border: "2px solid #333",
        cursor: "crosshair",
        imageRendering: "pixelated",
        background: "#000",
      }}
    />
  );
}
