# Tasks: Nearest Station Map SPA

**Input**: Design documents from `/specs/001-nearest-station-map-spa/`  
**Prerequisites**: [spec.md](./spec.md) ✅ | [plan.md](./plan.md) ✅

**Organization**: タスクはユーザーストーリー単位でグループ化し、独立したインクリメンタル実装・検証を可能にする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（他タスクと依存なし）
- **[Story]**: 対応するユーザーストーリー（US1〜US4）または共通（SHARED）

---

## Phase 1: セットアップ（共有インフラ）

**Purpose**: プロジェクト初期化・設定ファイル・型定義・ユーティリティなど、全ストーリーが依存する基盤を整備する

- [x] T001 [P] [SHARED] `package.json` を作成し Vue 3 / TypeScript / Vite / OpenLayers 依存を定義する
- [x] T002 [P] [SHARED] `vite.config.ts` を作成する（`base: '/'`、GitHub Pages 向けコメントあり）
- [x] T003 [P] [SHARED] `tsconfig.json` / `tsconfig.node.json` を作成する（strict モード有効）
- [x] T004 [P] [SHARED] `index.html` を作成する（`<div id="app">` / `<script type="module">` 含む）
- [x] T005 [P] [SHARED] `src/types/station.ts` に `Station` 型と `SearchParams` 型を定義する
- [x] T006 [P] [SHARED] `src/utils/geo.ts` を実装する（`haversineDistance` / `formatDistance` / `isValidCoordinate`）
- [x] T007 [P] [SHARED] `src/styles/global.css` を作成する（リセット・OL ポップアップスタイル含む）
- [x] T008 [P] [SHARED] `src/main.ts` を作成する（Vue アプリ起動・`global.css` インポート）

**Checkpoint**: `npm install` が成功し、プロジェクト構造が整った状態

---

## Phase 2: 基盤実装（全ストーリー共通ブロッカー）

**Purpose**: 全ストーリーが依存する service 層・composable を実装する

**⚠️ CRITICAL**: この Phase が完了するまで US1〜US4 の実装は開始できない

- [x] T009 [SHARED] `src/services/overpassService.ts` を実装する
  - `buildOverpassQuery(lat, lon, radiusMeters)`: Overpass QL 文字列生成（FR-005）
  - `fetchNearestStations(lat, lon, radiusMeters)`: `AbortController`（30 秒）付き POST リクエスト（FR-021）・レスポンス変換（node: lat/lon、way/relation: center.lat/center.lon）
  - `deduplicateStations(stations)`: 同名かつ座標差 0.001° 未満で距離が短い方を残す（FR-004）
- [x] T010 [SHARED] `src/composables/useNearestStations.ts` を実装する
  - `stations` / `isLoading` / `errorMessage` / `searchedParams` を `ref` で管理
  - `search(params)`: `isValidCoordinate` チェック → API 呼び出し → 距離順ソート → `slice(0, 10)` → 状態更新
  - エラーは catch して `errorMessage` にセット（FR-014 / FR-015）
  - 0 件時は「半径 Xm 以内に駅が見つかりませんでした」メッセージ（FR-014）
  - `clearResults()` 関数を提供

**Checkpoint**: `useNearestStations.search()` が Overpass API を呼び出し結果を返せる状態

---

## Phase 3: US1 — 地図クリックで最寄り駅を探す (Priority: P1) 🎯 MVP

**Goal**: 地図をクリックするだけで周辺駅が距離順に一覧・マーカー表示される（アプリの中核機能）  
**Independent Test**: アプリを起動 → 地図をクリック → 駅一覧と地図マーカーが表示される

### Implementation for US1

- [x] T011 [US1] `src/components/MapView.vue` を実装する
  - OpenLayers `Map` インスタンスのライフサイクル管理（`onMounted` / `onUnmounted`）
  - OSM タイルレイヤー・attribution 表示（FR-001 / FR-013）
  - 初期表示: 東京駅（緯度 35.681236 / 経度 139.767125）、ズーム 14（FR-002）
  - シングルクリック → `mapClick` emit（緯度・経度）（FR-003）
  - ダブルクリックは OpenLayers デフォルト（ズーム）のみ、検索しない（FR-020）
  - クリック地点マーカー（VectorLayer・赤丸）（FR-003）
  - 駅候補マーカー（VectorLayer・番号付き青丸）（FR-007）
  - 駅マーカークリック時に駅名・距離ポップアップ（Overlay）（FR-008）
  - `flyToStation(station)` / `panTo(lat, lon)` を `defineExpose` で公開（US4 / US3 向け）
  - `stations` props を `watch` して駅マーカーを更新
  - `isSearching` が `true` の間はクリックを無視（FR-012）
- [x] T012 [US1] `src/components/StationList.vue` を実装する（US1 範囲）
  - 駅一覧表示: 順位・駅名・距離（`formatDistance`）・OSM 種別（FR-009）
  - 0 件メッセージ表示（FR-014）
  - API エラーメッセージ表示（FR-014）
  - 未検索時プレースホルダー表示
- [x] T013 [US1] `src/App.vue` を実装する（US1 範囲）
  - `useNearestStations` composable を保持
  - `MapView` / `SearchPanel`（最低限）/ `StationList` を配置
  - `onMapClick(lat, lon)`: 検索中フラグを確認 → `search()` 呼び出し
  - レスポンシブレイアウト: PC 横並び（地図＋右パネル）/ モバイル縦並び（地図＋下パネル）（FR-016）
  - ヘッダー: アプリ名「Nearest Station Map」・説明文

**Checkpoint**: `npm run dev` → 地図クリック → 駅一覧と番号付きマーカーが表示される（US1 独立テスト合格）

---

## Phase 4: US2 — 検索半径を変更して探す (Priority: P2)

**Goal**: 検索半径（1,000m / 2,000m / 3,000m / 5,000m）を選択し、次のクリックに反映される  
**Independent Test**: 半径を変更 → 地図をクリック → 変更後の半径で検索される

### Implementation for US2

- [x] T014 [US2] `src/components/SearchPanel.vue` を実装する
  - 検索半径セレクター（`v-model:radiusMeters`、デフォルト 3,000m）（FR-006）
  - 半径変更時は自動再検索しない（FR-006 / Q1:A）
  - `isLoading` 中はセレクターを `disabled`（FR-012）
  - ローディングスピナー表示（FR-012）
  - 「地図をクリックして検索地点を指定してください」ヒント表示
- [x] T015 [US2] `src/App.vue` を更新し `SearchPanel` の `radiusMeters` を `useNearestStations.search()` に渡す

**Checkpoint**: 半径セレクター変更 → クリック → 変更後の半径で正しく検索される（US2 独立テスト合格）

---

## Phase 5: US3 — 現在地から最寄り駅を探す (Priority: P3)

**Goal**: 「現在地から探す」ボタンで GPS 座標を取得し、その地点で駅検索する  
**Independent Test**: HTTPS 環境でボタン押下 → 許可 → 現在地周辺の駅が表示される

### Implementation for US3

- [x] T016 [US3] `src/components/SearchPanel.vue` を更新する
  - 「現在地から探す」ボタンを追加（`geolocate` emit）（FR-011）
  - `isLoading` 中はボタンを `disabled`（FR-012）
- [x] T017 [US3] `src/App.vue` を更新する
  - `onGeolocate()` ハンドラーを実装:
    - `navigator.geolocation.getCurrentPosition()` を呼び出す（タイムアウト 10 秒）
    - 成功時: 現在地座標で `search()` を呼び出す
    - 成功時: `MapView.panTo(lat, lon)` で現在地座標に地図を移動（ズーム不変）（FR-011 / FR-019）
    - 失敗時: `GeolocationPositionError.code` に応じたメッセージを表示（FR-014）
    - 非対応ブラウザ時: 「Geolocation API 非対応」メッセージを表示
  - `geoError` ref を管理し UI に表示

**Checkpoint**: 現在地ボタン → 許可 → 現在地に地図移動 + 駅一覧表示（US3 独立テスト合格）

---

## Phase 6: US4 — 地図上で駅の場所を確認する (Priority: P4)

**Goal**: 「地図で見る」ボタンで地図が対象駅位置にアニメーション移動する  
**Independent Test**: 駅一覧の「地図で見る」ボタン押下 → 地図が対象駅位置にアニメーション移動

### Implementation for US4

- [x] T018 [US4] `src/components/StationList.vue` を更新する
  - 各駅アイテムに「地図で見る」ボタンを追加（`flyTo` emit）（FR-010）
- [x] T019 [US4] `src/App.vue` を更新する
  - `onFlyTo(station)` ハンドラーを実装し `mapViewRef.value?.flyToStation(station)` を呼び出す
  - `MapView` の `ref` を `mapViewRef` として保持し `defineExpose` 経由で `flyToStation` を呼ぶ

**Checkpoint**: 「地図で見る」→ 地図がアニメーション付きで該当駅位置に移動（US4 独立テスト合格）

---

## Phase 7: ポリッシュ・横断的関心事

**Purpose**: 全ストーリー完成後の品質向上・デプロイ対応・Constitution 対応

- [x] T020 [P] [SHARED] `npm run build`（`vue-tsc && vite build`）が成功することを確認する（SC-004）
- [x] T021 [P] [SHARED] `README.md` を更新する（概要・技術スタック・セットアップ・デプロイ手順・ODbL 表記）
- [x] T022 [P] [SHARED] `vite.config.ts` の GitHub Pages 向け `base` 設定をコメントで案内する（FR-017）
- [x] T023 [P] [SHARED] エラーハンドリングの網羅確認（FR-014 / FR-015）
  - Overpass API HTTP エラー / ネットワーク断 / 30 秒タイムアウト / 0 件 / 位置情報エラー
- [x] T024 [P] [SHARED] レスポンシブレイアウト動作確認（PC・モバイル）（FR-016 / SC-003）
- [x] T025 [P] [SHARED] **Constitution II 対応**: Vitest を導入し `src/utils/geo.ts` の単体テストを追加する（`haversineDistance` / `formatDistance` / `isValidCoordinate`）
- [x] T026 [P] [SHARED] **Constitution II 対応**: `src/services/overpassService.ts` の単体テストを追加する（`buildOverpassQuery` / `deduplicateStations`）
- [x] T027 [P] [SHARED] **Constitution IV 対応**: 基本アクセシビリティ確認（`role="status"` / `aria-live` / フォーカス管理）

**Checkpoint**: `npm run build` 成功 / テスト合格 / 全 SC（SC-001〜SC-006）の目視確認完了

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1（Setup）**: 依存なし — 即座に開始可能。全タスク [P] で並列実行可
- **Phase 2（基盤）**: Phase 1 完了後に開始。T009 → T010 の順（composable が service に依存）
- **Phase 3（US1）**: Phase 2 完了後に開始。T011 / T012 は並列可、T013 は T011・T012 完了後
- **Phase 4（US2）**: Phase 2 完了後（Phase 3 と並列開始可）。T015 は T014 完了後
- **Phase 5（US3）**: Phase 3 完了後（T011・T013 が必要）
- **Phase 6（US4）**: Phase 3 完了後（T011・T012・T013 が必要）
- **Phase 7（ポリッシュ）**: Phase 3〜6 の必要範囲完了後

### User Story Dependencies

- **US1（P1）**: Phase 2 完了後 → 独立実装・テスト可
- **US2（P2）**: Phase 2 完了後 → Phase 3 と並列可（SearchPanel は US1 の App.vue と統合）
- **US3（P3）**: US1（App.vue・MapView 完成）後
- **US4（P4）**: US1（StationList・MapView 完成）後

### Parallel Opportunities

| 並列グループ | タスク |
|---|---|
| Phase 1 全体 | T001〜T008（全て独立） |
| Phase 2 内 | T009 のみ先行、T010 は T009 完了後 |
| Phase 3 内 | T011 と T012 は並列可、T013 は両完了後 |
| Phase 4 内 | T014 → T015（順次） |
| Phase 3 と Phase 4 | 並列開始可 |
| Phase 7 全体 | T020〜T027（全て独立） |
