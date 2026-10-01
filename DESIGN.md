# Habitat PL/I → Web変換 設計書

## 1. システム概要

| 項目 | 内容 |
|------|------|
| システム名 | Habitat（1986 Lucasfilm MMO 復元） |
| 目的 | 世界初のグラフィカルMMO「Habitat」をPL/I（Stratus VOS）からPython+Reactに完全変換 |
| 種別 | リアルタイムWebアプリケーション（WebSocket） |
| 原作 | PL/I 26,218行（Stratus VOS / Commodore 64クライアント） |
| 実装規模 | Python + React 約4,622行（82%削減） |
| 公開URL | https://habitat-1986.onrender.com |

### 1.1 主要機能

- アバター操作（移動、ポーズ変更、発言）
- 108種類のオブジェクトクラス（ATM、銃、テレポーター、自販機等）
- リアルタイムマルチプレイヤー（WebSocket双方向通信）
- 7つのリージョン（町の広場、銀行、公園、お化け屋敷等）
- アイテムの拾う/置く/使う/装備
- 呪い・スタン等の状態異常システム
- レトロASCII風キャンバスレンダリング

---

## 2. 技術スタック

| レイヤー | 技術 | バージョン |
|----------|------|-----------|
| バックエンド | FastAPI + Uvicorn | 0.110+ |
| リアルタイム通信 | WebSocket | websockets 12.0+ |
| データベース | SQLite (async) | aiosqlite 0.20+ |
| 言語（サーバー） | Python | 3.12 |
| フロントエンド | React + TypeScript | React 19 / TS 5.9 |
| ビルドツール | Vite | 7.3 |
| デプロイ | Docker + Render.com | - |

---

## 3. ディレクトリ構成

```
habitat/
├── backend/
│   ├── main.py                 # FastAPIサーバー、WebSocketエンドポイント
│   ├── models.py               # データクラス（Avatar, Region, GameObject等）
│   ├── database.py             # SQLite非同期レイヤー
│   ├── region_processor.py     # リージョン状態管理、メッセージディスパッチ
│   ├── seed_data.py            # 初期ワールド（7リージョン、150+オブジェクト）
│   └── objects/                # 25ハンドラーモジュール（108+クラス対応）
│       ├── base.py             # BaseObject, OBJECT_REGISTRY
│       ├── avatar.py           # WALK, POSTURE, SPEAK, GRAB
│       ├── door.py             # DO(開閉), GO(リージョン移動)
│       ├── teleport.py         # PAY(起動), DO(テレポート)
│       ├── atm.py              # 銀行: 預入, 引出, 残高照会
│       ├── vendo.py            # 自販機: DO(巡回), PAY(購入)
│       ├── gun.py, weapons.py  # 武器: KNIFE, CLUB, GRENADE等
│       ├── containers.py       # BOX, CHEST, SAFE
│       ├── wearable.py         # HAT, JACKET, SHIRT, PANTS
│       ├── magic.py            # AMULET, RING, CRYSTAL_BALL
│       ├── creatures.py        # GHOST, HOUSE_CAT, BUREAUCRAT
│       ├── static.py           # TREE, BUSH, FOUNTAIN等37クラス
│       ├── portable.py         # FLASHLIGHT, SHOVEL等20+クラス
│       └── special.py          # HAND_OF_GOD, SEX_CHANGER
├── frontend/
│   └── src/
│       ├── App.tsx             # メインコンポーネント、状態管理
│       ├── types.ts            # TypeScript型定義、ClassID列挙（161エントリ）
│       ├── useWebSocket.ts     # WebSocketカスタムHook（自動再接続）
│       ├── GameCanvas.tsx      # レトロASCIIレンダラー（640x400 Canvas）
│       ├── ActionPanel.tsx     # コンテキスト依存アクションボタン
│       ├── LoginScreen.tsx     # プレイヤー名入力
│       ├── StatusBar.tsx       # HP、トークン、リージョン名
│       ├── ChatLog.tsx         # メッセージ履歴
│       ├── Inventory.tsx       # 所持アイテム表示
│       └── MiniMap.tsx         # リージョンナビゲーション
├── Dockerfile                  # マルチステージビルド
├── render.yaml                 # Render.comデプロイ設定
└── requirements.txt
```

---

## 4. システムアーキテクチャ

### 4.1 全体構成図

```
クライアント（ブラウザ）
  LoginScreen → プレイヤー名入力
       │
       ▼ WebSocket接続
  /ws/{player_name}
       │
       ▼
  FastAPIサーバー（Python）
  ├─ WebSocketエンドポイント
  ├─ Avatar読込/作成（DB）
  ├─ リージョン参加
  │
  ▼
  RegionProcessor（リージョン状態管理）
  ├─ OBJECT_REGISTRY[class_id]
  │   └─ 25ハンドラーモジュール
  │       → 108+クラスをディスパッチ
  ├─ broadcast()（全員へ送信）
  ├─ send_to()（個別送信）
  └─ SQLite（リージョン/オブジェクト/アバター永続化）
       │
       ▼ WebSocket JSON
  クライアント（React）
  ├─ GameCanvas（レトロ描画）
  ├─ ActionPanel（操作ボタン）
  ├─ ChatLog / Inventory / StatusBar
  └─ MiniMap（リージョン移動）
```

### 4.2 PL/I → Python 変換マッピング

```
PL/I (Stratus VOS)              Python (FastAPI)
─────────────────               ─────────────────
regionproc + s$task_wait_event → RegionProcessor + asyncio
Class_Table(0:255) ディスパッチ → OBJECT_REGISTRY: dict
n_msg/b_msg/p_msg/e_msg/r_msg → broadcast()/send_to()
hatchery.pl1 アバター生成      → Avatar dataclass + DB
Stratus keyed files            → SQLite + aiosqlite
C64クライアント(6502 ASM)       → React + Canvas 2D
```

---

## 5. API仕様

### 5.1 HTTPエンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | フロントエンド配信（index.html） |
| GET | `/api/regions` | 全リージョン一覧（JSON配列） |
| GET | `/api/regions/{region_id}` | リージョン詳細（オブジェクト・アバター含む） |

### 5.2 WebSocketエンドポイント

| パス | 説明 |
|------|------|
| WS `/ws/{player_name}` | 双方向JSON通信（ゲームプレイ全般） |

**クライアント→サーバー:**
```json
{ "action": "WALK", "noid": 12, "args": { "x": 80, "y": 130 } }
```

**サーバー→クライアント:**
```json
{ "type": "WALK", "noid": 12, "x": 80, "y": 130 }
```

**メッセージタイプ（15種類）:**
INIT, REGION_CHANGE, AVATAR_ENTER, AVATAR_LEAVE, WALK, POSTURE, SPEAK, GRAB, HAND, DOOR_TOGGLE, GUN_SHOT, ACTION_RESULT, ATM_RESULT, VENDO_DISPLAY, TELEPORT_READY

---

## 6. データベース設計

### 6.1 テーブル構成

**regions テーブル:**
| カラム | 型 | 説明 |
|--------|-----|------|
| region_id | PK | リージョンID |
| name | TEXT | リージョン名 |
| terrain_type | INT | 0=屋内, 1=屋外 |
| x_size, y_size | INT | リージョン寸法 |
| neighbor_west/east/north/south | INT | 隣接リージョンID |

**objects テーブル:**
| カラム | 型 | 説明 |
|--------|-----|------|
| noid | PK AUTO | オブジェクトインスタンスID |
| class_id | INT | ClassID列挙値（161種類） |
| region_id | FK | 所属リージョン |
| x, y | INT | 座標 |
| container_noid | INT | 0=地面、それ以外=所有者noid |
| extra | JSON | クラス固有データ |

**avatars テーブル:**
| カラム | 型 | 説明 |
|--------|-----|------|
| noid | PK | アバターID |
| name | UNIQUE | プレイヤー名 |
| health | INT | HP |
| bank_account | INT | 銀行残高 |
| tokens_in_hand | INT | 所持トークン |
| curse_type | INT | 呪い状態（0=なし, 1=COOTIES, 2=SMILEY, 4=FLY） |
| deaths, kills, travel | INT | 統計情報 |

---

## 7. オブジェクトクラスシステム

### 7.1 アクション定義（13種類）

| ID | アクション | 説明 |
|----|-----------|------|
| 1 | GO | 移動（ドア通過等） |
| 2 | DO | 操作（開閉、使用、攻撃） |
| 4 | GRAB | 拾う |
| 5 | HAND | 手に持つ/渡す |
| 6 | POSTURE | ポーズ変更（9種類） |
| 7 | SPEAK | 発言 |
| 8 | WALK | 歩行移動 |
| 11 | PAY | 支払い（自販機、テレポート） |

### 7.2 主要ハンドラーと対応クラス

| ハンドラー | 対応クラス数 | 代表クラス |
|-----------|------------|-----------|
| StaticHandler | 37 | TREE, BUSH, FOUNTAIN, BUILDING, WALL |
| PortableHandler | 20+ | FLASHLIGHT, SHOVEL, COMPASS, BOTTLE |
| WeaponHandler | 6 | KNIFE(15dmg), CLUB(20), GRENADE(40,AoE) |
| WearableHandler | 4 | HAT, JACKET, SHIRT, PANTS |
| MagicHandler | 6 | AMULET, RING, CRYSTAL_BALL, MAGIC_LAMP |
| ContainerHandler | 4 | BOX, CHEST, SAFE, DISPLAY_CASE |
| CreatureHandler | 3 | GHOST, HOUSE_CAT, BUREAUCRAT |

### 7.3 ディスパッチ方式

```python
# PL/IのClass_Table vtable → Python辞書ディスパッチ
OBJECT_REGISTRY: dict[int, BaseObject] = {}

# register_all() で108+クラスを登録
OBJECT_REGISTRY[ClassID.DOOR] = DoorHandler()
OBJECT_REGISTRY[ClassID.ATM] = ATMHandler()
# ...

# アクション実行
handler = OBJECT_REGISTRY.get(obj.class_id)
result = handler.dispatch(action, region, noid, args)
```

---

## 8. フロントエンド設計

### 8.1 レンダリング

- 640x400 Canvas（レトロASCII風）
- リージョン別カラーテーマ（Town Square=ダーク、Bank=ゴールド、Park=グリーン）
- クリックで歩行・オブジェクト操作
- ClassID別のASCIIスプライト + 色定義（161エントリ）

### 8.2 WebSocket自動再接続

- 切断時2秒後に自動再接続
- 接続状態をStatusBarに表示
- JSON形式のメッセージパース

---

## 9. 初期ワールド構成

| リージョン | 特徴 | 主要オブジェクト |
|-----------|------|----------------|
| Town Square | 中央広場 | 噴水、掲示板、街灯 |
| Bank | 銀行 | ATM、カウンター |
| General Store | 雑貨店 | 自販機、陳列棚 |
| Park | 公園 | 木、花、ベンチ |
| Haunted House | お化け屋敷 | ゴースト、蜘蛛の巣 |
| Teleport Station | テレポート駅 | テレポーター |
| Lounge | ラウンジ | ジュークボックス、椅子 |

---

## 10. デプロイ構成

**Dockerマルチステージビルド:**
1. ステージ1（Node.js 20）: フロントエンドビルド（`npm run build`）
2. ステージ2（Python 3.12）: バックエンド + ビルド済みフロントエンド配信

**Render.com設定（render.yaml）:**
- サービスタイプ: Web Service
- ビルド: Docker
- ポート: 8080
