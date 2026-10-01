# habitat

1986年の PL/I 製世界初のグラフィカルMMO「Habitat」を Python (FastAPI + WebSocket) と React (Canvas) に変換した Web 版です。

・backend: FastAPI、地域プロセッサ、オブジェクトハンドラ（`backend/objects/`）、SQLite
・frontend: React + Canvas
・設計メモ: [DESIGN.md](DESIGN.md)
・原典との差分（欠落・簡略化）: [GAP_ANALYSIS.md](GAP_ANALYSIS.md)

## テスト・ツール

・テスト: `python -m pytest tests`（28件。固有アクション、タイマー、呪い、永続化、変換ツール）
・フロントのビルド: `cd frontend && npm run build`
・`tools/extract_fortunes.py`: 原典 fortune_machine から 90 文を `backend/fortunes_data.py` へ抽出
・`tools/rdl_to_regions.py <habitatツリー> <out.json>`: 原典 `.rdl` 地域記述を JSON へ変換（504 地域、オブジェクト 5,465）
