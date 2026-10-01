# GAP_ANALYSIS: Habitat (PL/I -> Python + React)

作成日: 2026-10-01 / 方法: 静的比較（原典と変換物のソース精読）。実行検証はしていない
原典: `data/raw/github/habitat/chip/habitat/stratus`（262ファイル 26,286行、`class_*.pl1` 109本）＋ `habitat/Regions` の `.reg` 1,649本
変換物: `backend` 2,693行 + `frontend` 1,929行 = 4,622行（実測）

## 0. DESIGN.md との照合（4.2節ほか）

DESIGN.md（285行）は「完全変換」「108種類」「161 ClassID」「25ハンドラーモジュール」と記載している。実コードとの照合結果は次のとおり。

| DESIGN.md の記載 | 実コード | 判定 |
|---|---|---|
| 「完全変換」 | 108クラスは登録済みだが、大半は汎用ハンドラ。固有アクション・タイマー・永続化が未実装 | 過大（要修正） |
| 108種類のオブジェクト | backend/objects/__init__.py register_all() が 108 ClassID を登録。原典 class_*.pl1 は109本で、不一致は GATE/TEST（原典のみ）と SIGN_OLD（変換のみ） | 概ね一致（登録数の一致であり機能の一致ではない） |
| 161 ClassID | models.py の ClassID は 108 エントリ | 不一致 |
| 25ハンドラーモジュール | backend/objects/ に .py 25本（__init__/base含む） | 一致（ただし多くは汎用） |
| 4.2節 PL/I Class_Table -> Python レジストリ + handle_ACTION | region_processor.py の handle_{action} ディスパッチとして実在 | 実装済み |
| 4.2節 n/b/p/e/r_msg -> WebSocket | region_processor.py の broadcast_all/broadcast/send_to | 実装済み |
| 4.2節 VOS keyed files -> SQLite | database.py（137行）。保存されるのは avatars のみ | 簡略化（オブジェクト・地域状態は非永続） |
| 15 メッセージ種別 / 13 アクション | models.py の Action enum は HELP, GO, DO, GRAB, HAND, POSTURE, SPEAK, WALK, PUT, THROW, MAGIC, PAY, CLOSE, OPEN | 数は enum 通り。原典の各クラス固有アクションは含まない |
| 実装規模（backend 約890行と指示文にあった数字） | backend 実測 2,693行 | 指示文の数字が誤り。実測は 2,693 |

## 1. 分類表

| 原典の機能単位 | 原典 | 変換先 | 分類 | 根拠 |
|---|---|---|---|---|
| クラスレジストリ/ディスパッチ | habitat.pl1 / class_table | objects/__init__.py:27-137, region_processor.py | 実装済み | 108 ClassID 登録 |
| 地域ブロードキャスト/個別送信 | messages.pl1 (649) | region_processor.py (197) | 実装済み | broadcast_all/broadcast/send_to |
| アバター基本（WALK/SPEAK/HELP/GRAB/HAND） | class_avatar.pl1 (483) | objects/avatar.py | 実装済み | stun_count 判定 avatar.py:50 |
| アバター固有（ESP, TOUCH, SIT, NEWREGION, DISCORPORATE, FNKEY） | class_avatar.pl1 | なし | 欠落 | Action enum に無い |
| 呪い（COOTIES/SMILEY/MUTANT/FLY） | curses.pl1 (96) | avatar.py:22 buzzify のみ | 欠落（一部残骸） | TOUCH 経由の感染・カウンタ・免疫が無く、呪いは取得不能 |
| ドア/テレポート/ATM/自販機 | class_door, teleport, atm, vendo_front | door.py, teleport.py, atm.py, vendo.py | 簡略化 | ATMのDEPOSIT/WITHDRAW、vendo VSELECT/PAY の固有挙動なし。Vendo PAY は商品を生成しない |
| 武器・ダメージ | actions_weapon.incl.pl1（固定20ダメージ、HIT/DEATH） | objects/weapons.py:11 DAMAGE_TABLE | 簡略化（改変） | 原典は一律20。変換は武器別値+乱数、対象は最近接アバター |
| 魔法 | magic.pl1 (903)、29種 | objects/magic.py | 簡略化 | 29魔法（身長変更、送還、capture_flag、lottery、money_tree 等）が定型文10種+ランダム回復/攻撃に置換 |
| 装着物（頭） | class_head WEAR/REMOVE | objects/wearable.py | 簡略化 | 帽子/服を WEAR トグルで共通化 |
| 機械類 | class_coke/fortune/pawn 等 | objects/machines.py | 簡略化・追加 | coke_machine（HP+20）と fortune リストは変換側の創作。pawn_machine は何もしない |
| クリーチャー | ghost（原典は死亡プレイヤーの幽霊状態: ghost_WALK/NEWREGION/CORPORATE） | objects/creatures.py:58-65 | 簡略化（別物） | 変換は30%で攻撃するNPC。原典の幽霊は攻撃しない |
| Hand of God | class_hand_of_god（HELPのみ） | objects/special.py:58-64 | 追加 | 全回復+1000トークンは変換側の創作 |
| 性転換器 | class_sex_changer | objects/special.py | 簡略化 | スタイル切替 |
| 固有アクション持ちの約30クラス | bottle FILL/POUR, changomatic CHANGE, compass DIRECT, die ROLL, drugs TAKE, elevator ZAPTO, grenade PULLPIN, jukebox PAY/SELECT, magic_lamp RUB/WISH, shovel DIG, spray_can SPRAY, stereo LOAD, stun_gun STUN, tokens PAY/SPLIT, windup_toy WIND ほか | static/portable/container 等の汎用ハンドラ | 欠落 | 固有アクションは Action enum に無く、HELP+定型文のみ |
| 紙/メール | class_paper READ/WRITE/PSENDMAIL, mail 処理 | objects/paper.py, mailbox.py | 簡略化 | メモリ上のみで再起動で消える |
| 地域プロセス（ProcessTact, schedule_event, 定員監視, UserList6, ghost list, oracle） | regionproc.pl1 (5,455) | region_processor.py (197) | 欠落 | タイマー・定員・幽霊リスト・オラクルなし |
| 隣接地域歩行 / change_regions | regionproc / habitat | main.py (219) の GOTO ミニマップ | 簡略化 | 方向歩行ではなく GOTO |
| 永続化・チェックポイント・統計・履歴 | regionproc, habitat_db (1,426) | database.py:111 | 簡略化/欠落 | avatars のみ保存。curse_type は ON CONFLICT 更新対象外。container_noid, gr_state 等は非永続。統計・turf・履歴なし |
| ログイン/ルームプロセス | habitat.pl1 (2,379) | main.py WS /ws/{name} | 簡略化 | 認証・ユーザーリストの管理なし |
| ハッチェリー（アバター/頭/紙/トークン生成、turf） | hatchery.pl1 (941) | database.py の簡易作成 | 簡略化（turf欠落） | |
| ヘルパー（kill_avatar, pay_to, spend_check, auto_teleport, region_entry_daemon） | helpers.pl1 (1,106) | 各 handler 内に分散 | 簡略化 | 共通処理としての対応物は無い |
| ワールドデータ | Regions 1,649 .reg | seed_data.py（7地域・約80オブジェクト） | 欠落 | 全世界の 0.4% |
| C64クライアント描画 | C64 クライアント | frontend TerminalCanvas 等 (1,929行) | 簡略化 | HAND（落とす）/POSTURE の送信UIなし |
| 管理・リージョンエディタ | 管理/編集ツール | なし | 対象外候補 | |

## 2. 行数差の内訳

原典 26,286行 -> 変換 4,622行。

・regionproc 5,455行: 地域プロセッサ 197行へ。タイマー・容量・メール・オラクル・永続化が未移植
・habitat 2,379 + habitat_db 1,426 + hatchery 941 + helpers 1,106: 約5,850行 -> main.py/database.py/seed_data 等 約700行
・magic 903行 -> 魔法 1ファイルに定型文化
・class_*.pl1 109本 → 汎用ハンドラ化（固有アクションの大半が脱落）
・Regions 1,649 .reg: 行数に含まれない世界データ。変換側は 7 地域
・変換側 frontend 1,929行は原典C64クライアント部分に対応（原典は別言語・別リポジトリ領域）

reports/HABITAT_ANALYSIS_REPORT.md は第1段階を「代表約15クラス」、第2段階（残り90クラス超、魔法、呪い、統計、リージョンエディタ）を将来としており、その第2段階が未着手のまま「完全変換」と書かれている状態である。

## 3. 4分類の候補

・実装済み: ディスパッチ、メッセージ、基本アバター動作、アバター永続化
・簡略化: 武器、魔法、ATM/自販機/テレポート、装着物、メール、地域移動
・欠落: 呪い、アバター固有アクション6種、約30クラスの固有アクション、タイマー/定員/オラクル、オブジェクト永続化、世界データ 1,649 地域
・追加（原典になし）: coke_machine、Hand of God の全回復、ghost の攻撃、武器ダメージ表
・対象外候補: リージョンエディタ、管理系

## 4. 是正提案（優先度順）

| 優先 | 内容 | 規模 |
|---|---|---|
| 1 | DESIGN.md の「完全変換」「161 ClassID」を実態に訂正（「108クラス登録、固有挙動は一部」） | 極小 |
| 2 | 創作した挙動（coke, Hand of God, ghost 攻撃, 武器ダメージ表）を原典準拠に戻すか「変更点」として明記 | 小（約100行） |
| 3 | 呪い（curses.pl1 相当）と TOUCH/ESP/SIT/NEWREGION/DISCORPORATE | 中（約300行） |
| 4 | 固有アクションを持つクラス約30種の実装（原典 class_*.pl1 を1対1で） | 大（約1,500行） |
| 5 | オブジェクト/地域状態の永続化、curse_type 保存 | 中（約300行） |
| 6 | 魔法29種の原典準拠実装 | 中（約500行） |
| 7 | 地域タイマー（ProcessTact）、定員、ghost list、オラクル | 大（約800行） |
| 8 | .reg ローダー（1,649地域の取り込み） | 大（約600行+データ変換） |

## 5. 不明点

・各 class の固有アクションは原典の `class_*.pl1` のアクションテーブルから抽出した。PL/I 内部の細かい分岐までは追っていない
・原典との実行比較はしていない（静的比較のみ）

## 6. 是正記録（2026-10-01）

・是正1（DESIGN.md 訂正）完了: 「完全変換」を「部分変換」に、「161 ClassID」を実測の「108」に訂正。世界データは原典 1,649 地域のうち 7 地域（約0.4%）、原典にない創作（coke_machine、Hand of God 全回復、ghost 攻撃、武器別ダメージ表）を DESIGN.md に明記。コード修正なし
・分類: 上記は「文書の過大記載の是正」（欠落・簡略化は引き続き未是正）
・未是正（別途対応）: 是正2〜8（創作挙動の原典準拠化、呪い・アバター固有アクション、固有アクション約30クラス、永続化、魔法29種、地域タイマー、.reg ローダー）

## 7. 是正記録（2026-10-02、原典準拠化）

テスト: `tests/test_original_actions.py` 28件（WSL Ubuntu、pytest）全通過。frontend の `npm run build` 通過。実行比較（原典実機との突き合わせ）はしていない。

### 7.1 4分類（是正後）

実装済み（原典 class_*.pl1 と1対1で変換、`backend/objects/original_actions.py`）
・coke_machine PAY（$5、HP回復なし）、fortune_machine PAY（$2、原典90文を `fortunes_data.py` に抽出、`tools/extract_fortunes.py`）、pawn_machine MUNCH
・generic_ATTACK（knife/club/gun。固定20ダメージ、スタン時・weapons_free地域で不可、DEATHで kill_avatar）
・die ROLL、game_piece、compass DIRECT、drugs TAKE/HELP（回復・毒・黒化）、spray_can SPRAY、shovel DIG、windup_toy WIND、bottle FILL/POUR、changomatic CHANGE、sex_changer SEXCHANGE、stun_gun STUN、fake_gun FAKESHOOT/RESET、tokens SPLIT、escape_dev BUGOUT、sensor SCAN、matchbook、tape、garbage_can FLUSH、aquarium FEED
・grenade PULLPIN（20秒信管、Tactで爆発、全アバター20ダメージ）、magic_lamp RUB/WISH（30秒×2のジーニー待機タイマー）
・Tactスケジューラ（`RegionProcessor.tact/clear_tact/process_tact/tact_loop`、秒単位）
・呪い curses.pl1（TOUCH、COOTIES/SMILEY/MUTANT/FLY、カウンタ、免疫、buzzify の b/B 規則）
・永続化（オブジェクト、持ち物、curse_type/curse_counter/免疫、weapons_free、30秒チェックポイント、切断・地域移動・終了時保存、DB列の自動マイグレーション）
・kill_avatar の original 準拠（持ち物を落とす、銀行20%没収、死亡数加算）
・DO ボタンは各クラスの主アクションへ割り当て（`PRIMARY_DO`。UI側の対応でWeb版固有）

簡略化
・トークンは整数 `tokens_in_hand`（原典は TOKENS オブジェクト）。`adjacent()` は原典の old_adjacent（常に真）
・kill_avatar の復活は現地域（原典は auto_teleport で turf へ）
・呪いの頭: 頭オブジェクトが無いため `Avatar.style` を head.style の代用にした。「頭なしは免疫」規則は未再現
・boomerang の戻り: 原典は schedule_event がスタブで戻らない。Web版は 10〜30 秒後に戻す（意図的変更、理由は「動かない機能を移植しても意味がないため」）
・aquarium: 原典も schedule_event スタブのため FEEDING で止まる（同じ挙動）
・magic_lamp の WISH は原典 message_to_god（ソース未入手）の代わりにサーバログへ出力
・test_bit の桁番号は LSB=0 と仮定（原典の PL/I bit 配置は未検証）
・保留中の Tact（導火線中の手榴弾など）は再起動で消える

欠落（未着手）
・アバター ESP/SIT/NEWREGION/DISCORPORATE/FNKEY、avatar PAY
・jukebox/stereo/elevator/vendo の固有アクション、tokens PAY、paper、mail、magic.pl1 の29魔法
・定員監視・ghost list・オラクル、turf、hatchery、統計・履歴
・pawn_machine の item_value（原典テーブル未入手のため `extra["value"]` 参照）
・原典データの地域ロード（下記 7.2）

追加（原典になし）
・SWITCH の ON/OFF（原典クラス表に対応なし）
・GOTO ミニマップ、`PRIMARY_DO`、最近接アバターを標的に補う処理（クライアントが標的IDを送らないため）

除去した創作: coke の HP+20、10文の偽 fortune、Hand of God の全回復+1000トークン（原典は HELP のみ）、ghost の攻撃（原典は攻撃なし）、武器別ダメージ表（原典は一律20）、gun の弾数、changomatic/sex_changer のスタイル循環。意図的に残した創作は boomerang の戻りのみ。

### 7.2 世界データ 1,649 地域の変換可否

調査結果: `.reg` は 512 バイト単位のコンパイル済みバイナリ（3,299 本）で、機械変換には構造定義の逆解析が必要で見合わない。テキストの `.rdl`（1,042 本）が地域記述の原典で、機械変換が可能。
実施: `tools/rdl_to_regions.py` が `.rdl` を JSON（地域名・隣接・オブジェクト入れ子・スロット値）へ変換する。実測は、重複名を除いて 504 地域、オブジェクト 5,465 個、未知クラス 0、隣接参照の未解決 6（`slur/foo.rdl` 等テスト用ファイルの外部参照）。
未実施: JSON を DB/seed へ取り込む処理と、各クラスの属性スロット（sign の文字列、teleport のアドレス等）の意味づけ。原典 1,649 のうち `.rdl` として残るのは 504 で、残り約 1,145 地域は `.rdl` が現存しない（`.reg` のみ）。工数見積: 取り込み+スロット意味づけで約 600 行、`.reg` 逆解析は別途大。
