# Implementation Plan: Nearest Station Map SPA

**Branch**: `001-nearest-station-map-spa` | **Date**: 2026-05-28 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-nearest-station-map-spa/spec.md`

## Summary

OpenStreetMap をベースにした最寄り駅表示 SPA。ユーザーが地図上をシングルクリックすると Overpass API で周辺駅を検索し、Haversine 距離順に最大 10 件を一覧・マーカー表示する。バックエンドなし・静的ホスティング前提。Vue 3 Composition API + OpenLayers による純粋フロントエンド構成。

## Technical Context

**Language/Version**: TypeScript 5.8 / Node.js 20+  
**Primary Dependencies**: Vue 3.5, OpenLayers 10.4, Vite 6.3, vue-tsc 2.2  
**Storage**: なし（セッション内メモリのみ、永続化は MVP スコープ外）  
**Testing**: 未設定（MVP フェーズ。Constitution II に基づき後続タスクで追加）  
**Target Platform**: ブラウザ（モダンブラウザ全般）/ GitHub Pages / Vercel（静的 SPA）  
**Project Type**: Web SPA（フロントエンドのみ）  
**Performance Goals**: 地図クリックから一覧表示まで通常環境で 10 秒以内（SC-001）  
**Constraints**: バックエンドなし・API キー不要・静的ファイルのみ配信・Overpass API 直接呼び出し  
**Scale/Scope**: 個人利用・非商用。同時接続数の要件なし

## Constitution Check

プロジェクト憲章（`.specify/memory/constitution.md` v1.0.0）との照合:

| 原則 | 判定 | 備考 |
|------|------|------|
| I. 可読性・保守性を最優先 | ✅ | コンポーネント分割・service 層・composable による責務分離 |
| II. すべてのコンポーネントに単体テスト | ⚠️ | MVP フェーズでは未実装。後続タスク（Task 7）で追加 |
| III. まず動くコードを書く | ✅ | MVP 実装優先。パフォーマンス最適化は別フェーズ |
| IV. アクセシビリティは WCAG 2.1 AA | ⚠️ | MVP では基本的な対応（role/aria-live）のみ。後続タスクで詳細対応 |

> **⚠️ 留意事項**: テストと WCAG 完全準拠は MVP 後のフェーズで対応。Plan フェーズ終了前に /speckit.tasks でタスクとして登録すること。

## Project Structure

### Documentation (this feature)

```text
specs/001-nearest-station-map-spa/
├── spec.md              # フィーチャー仕様書（Clarified）
├── plan.md              # このファイル
├── checklists/
│   └── requirements.md  # 仕様品質チェックリスト
└── tasks.md             # /speckit.tasks コマンドで生成（未作成）
```

### Source Code

```text
src/
├── main.ts                     # Vue アプリ起動・グローバル CSS インポート
├── App.vue                     # ルートコンポーネント。レイアウト・イベントハブ
├── components/
│   ├── MapView.vue             # OpenLayers 地図・マーカー・ポップアップ（地図固有処理を集約）
│   ├── SearchPanel.vue         # 検索半径セレクター・現在地ボタン・ローディング表示
│   └── StationList.vue         # 駅一覧・エラー表示・「地図で見る」ボタン
├── composables/
│   └── useNearestStations.ts   # 検索状態（isLoading/errorMessage/stations）と search() を提供
├── services/
│   └── overpassService.ts      # Overpass QL 生成・API 呼び出し・重複除外
├── utils/
│   └── geo.ts                  # Haversine 距離計算・距離フォーマット・座標バリデーション
├── types/
│   └── station.ts              # Station 型・SearchParams 型
└── styles/
    └── global.css              # リセット・全体レイアウト・OL ポップアップスタイル
```

**Structure Decision**: 単一プロジェクト構成（Option 1）。バックエンドなし・SPA のみのため frontend/backend 分割は不要。コンポーネントは責務ごとに分割し、OpenLayers 固有処理は MapView.vue に集約する。

## Component Responsibilities

### App.vue（オーケストレーター）
- `useNearestStations` composable を保持
- `MapView` / `SearchPanel` / `StationList` を組み合わせてレイアウト
- `mapClick` / `geolocate` / `flyTo` イベントを各コンポーネントへ橋渡し
- レスポンシブレイアウト（PC: 横並び / モバイル: 縦並び）

### MapView.vue（地図）
- OpenLayers `Map` インスタンスのライフサイクル管理（`onMounted` / `onUnmounted`）
- シングルクリックイベント → `mapClick` emit（緯度・経度）
- ダブルクリック → OpenLayers デフォルトのズーム動作（FR-020）
- クリック地点マーカー（VectorLayer）と駅候補マーカー（VectorLayer・番号付き）
- 駅マーカークリック時のポップアップ（Overlay）表示
- `flyToStation(station)` を `defineExpose` で公開
- `stations` props 変更を `watch` して駅マーカーを更新

### SearchPanel.vue（検索設定）
- 検索半径セレクター（`v-model:radiusMeters`）
- 「現在地から探す」ボタン（`geolocate` emit）
- `isLoading` 中は全操作を `disabled`
- ローディングスピナーと「地図をクリックしてください」ヒント表示

### StationList.vue（結果表示）
- 駅一覧のレンダリング（順位・駅名・距離・OSM 種別）
- 「地図で見る」ボタン → `flyTo` emit
- エラーメッセージ・0 件メッセージ・未検索プレースホルダーの出し分け

### useNearestStations.ts（検索ロジック）
- `stations` / `isLoading` / `errorMessage` / `searchedParams` を `ref` で管理
- `search(params)`: バリデーション → API 呼び出し → ソート → 状態更新
- エラーは catch して `errorMessage` にセット（アプリクラッシュ防止）

### overpassService.ts（外部 API）
- `buildOverpassQuery(lat, lon, radius)`: Overpass QL 文字列生成
- `fetchNearestStations(lat, lon, radius)`: `AbortController`（30 秒）付き POST リクエスト・レスポンス変換
- `deduplicateStations(stations)`: 同名・近座標の重複除外（同名かつ座標差 0.001° 未満で距離が短い方を残す）

### geo.ts（計算ユーティリティ）
- `haversineDistance(lat1, lon1, lat2, lon2): number`
- `formatDistance(meters): string`（1,000m 未満: `xxx m` / 以上: `x.x km`）
- `isValidCoordinate(lat, lon): boolean`

## Data Flow

```
ユーザー操作（地図クリック / 現在地ボタン）
        ↓ emit: mapClick(lat, lon) / emit: geolocate
App.vue: onMapClick / onGeolocate
        ↓ useNearestStations.search({ lat, lon, radiusMeters })
overpassService.fetchNearestStations()
        ↓ Overpass API (POST)
        ↓ レスポンス変換 → deduplicateStations → haversineDistance → sort → slice(0, 10)
useNearestStations: stations.value 更新
        ↓ props: stations (watch)
MapView.vue: 駅マーカー更新
StationList.vue: 一覧再レンダリング
```

## API Design

### Overpass API

- **エンドポイント**: `https://overpass-api.de/api/interpreter`
- **メソッド**: POST
- **Content-Type**: `application/x-www-form-urlencoded;charset=UTF-8`
- **Body**: `data=<Overpass QL>`
- **クエリ対象タグ**: `railway~"station|halt"` / `public_transport=station`（`["name"]` 必須）
- **出力**: `out center tags`（way/relation の中心座標を取得するため）

### エラーハンドリング方針

| シナリオ | 処理 |
|---|---|
| HTTP 4xx / 5xx | `throw new Error(...)` → `useNearestStations` catch → `errorMessage` |
| ネットワーク断 | `fetch` が reject → 同上 |
| 30 秒タイムアウト | `AbortController` で signal を `fetch` に渡す。`AbortError` を catch して「検索がタイムアウトしました」メッセージを表示 |
| 0 件 | `errorMessage` に「半径 Xm 以内に駅が見つかりませんでした」 |
| 座標不正 | `isValidCoordinate` チェック → `errorMessage` |
| 位置情報拒否 | `GeolocationPositionError.code` に応じたメッセージ |

## Deployment

| ターゲット | 設定 |
|---|---|
| Vercel | `base: '/'`（デフォルト）。Vite SPA として自動検出 |
| GitHub Pages | `vite.config.ts` の `base` をリポジトリ名（例: `/nearest-station-map/`）に変更してビルド |
| ビルドコマンド | `npm run build`（`vue-tsc && vite build`） |
| 出力先 | `dist/` |

## Complexity Tracking

Constitution Check で挙げた留意事項:

| 事項 | 理由 | 対応方針 |
|------|------|----------|
| テスト未実装（Constitution II 違反） | MVP フェーズ優先・テストフレームワーク未設定 | Task 7 として `/speckit.tasks` に登録し、Vitest 導入後に `utils/geo.ts` と `services/overpassService.ts` の単体テストを優先実装 |
| WCAG 2.1 AA 完全準拠（Constitution IV 一部未対応） | MVP では `role` / `aria-live` のみ対応 | Task 8 としてフォーカス管理・カラーコントラスト・スクリーンリーダー対応を追加 |
