---
title: "Overpass APIが不安定だったのでVue 3 + 静的JSONで最寄り駅マップを作った話"
emoji: "😊"
type: "tech"
topics: ["vue", "typescript", "openstreetmap", "githubcopilot", "oss"]
published: false
---

# はじめに

今回は GitHub Copilot（エージェントモード）を活用して、地図上の任意の地点から最寄り駅を探せる Web アプリを Vue 3 + TypeScript で作った話をまとめます。こういうものが欲しい。という構想から、仕様策定・実装・モバイル対応・デプロイまで一気に進められたので、その流れを紹介します。

完成物はこちらです。

https://yutaka-art.github.io/nearest-station-map/

![](/images/54a4b18baccc4b/001.png)

# 作ったもの

**駅どこサーチ** は 地図をタップ/クリックするだけで、その地点周辺の駅を距離順に最大10件表示するシンプルな Web アプリです。

- 地図上の任意地点をクリック → 周辺駅を距離順に表示
- 検索半径は 1,000 / 2,000 / 3,000 / 5,000m から選択できる
- 現在地（Geolocation API）からの検索にも対応
- 駅マーカーをクリックするとポップアップで駅名・距離を確認できる
- スマートフォンでも使いやすいようにモバイル対応済み（iPhone 13 Pro 基準）

地図データには OpenStreetMap、地図ライブラリには OpenLayers を使っています。Google Maps も候補でしたが、API キーや課金設定の手間を考えると、個人開発の最初のひとつには OpenStreetMap ベースの構成がちょうどよいと感じました。

駅データについては、当初 **Overpass API** をリアルタイムで呼び出す方式で実装していました。しかし実際に動かしてみると、タイムアウトや応答遅延が頻発してしまいました。最終的に、全国駅データを事前に一括取得して静的 JSON ファイルとして配信する方式に切り替えることで解消できたので、その経緯も含めて紹介します。

なお、OpenStreetMap や Overpass API は「無制限に使える無料サービス」ではなく、コミュニティや寄付・スポンサーに支えられた公共性の高いリソースです。過度なリクエストを避ける・帰属表示を行う・必要以上にデータを取得しない、といった配慮は引き続き必要です。

# 技術スタック

| 項目 | 採用技術 |
|---|---|
| フレームワーク | Vue 3（Composition API） |
| 言語 | TypeScript（strict モード） |
| ビルドツール | Vite |
| 地図ライブラリ | OpenLayers |
| 背景地図 | OpenStreetMap |
| 駅データ | 静的 JSON（Overpass API で事前一括取得）|
| テスト | Vitest |
| ホスティング | GitHub Pages（GitHub Actions で自動デプロイ） |

# 実装の要点

## Overpass API で駅データを取得する（初期実装）

最初に Overpass API をリアルタイムで呼び出す設計で実装しました。地図クリック地点の座標を中心に、Overpass QL というクエリ言語で OSM のデータを取得します。

```typescript
// src/services/overpassService.ts（抜粋）
export function buildOverpassQuery(
  lat: number,
  lon: number,
  radiusMeters: number,
): string {
  return `
    [out:json][timeout:25];
    (
      node["railway"="station"](around:${radiusMeters},${lat},${lon});
      node["railway"="halt"](around:${radiusMeters},${lat},${lon});
    );
    out body;
  `
}
```

取得したノードは距離でソートし、最大 10 件に絞り込みます。
OpenStreetMap のデータでは、同じ駅に関する情報が複数の要素として登録されていることがあるため、駅名をもとに簡易的な重複排除も行っています。

MVP としてはこれで十分ですが、より厳密に扱う場合は `node` だけでなく `way` や `relation`、`public_transport=station` なども含めて取得し、`center` 情報を使って代表座標を扱う設計にするとよさそうです。

## 距離計算は Haversine 公式で

緯度経度の 2 点間距離は、地球の球面を考慮した Haversine 公式で計算しています。
以前、砂防・防災系のシステムで震源地や到達域との距離を扱う処理に触れたことがあり、このあたりの考え方には少し馴染みがありました。

```typescript
// src/utils/geo.ts（抜粋）
export function haversineDistance(
  lat1: number, lon1: number,
  lat2: number, lon2: number,
): number {
  const R = 6371000
  const φ1 = (lat1 * Math.PI) / 180
  const φ2 = (lat2 * Math.PI) / 180
  const Δφ = ((lat2 - lat1) * Math.PI) / 180
  const Δλ = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(Δφ / 2) ** 2 +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}
```

このアプリが表示するのは「直線距離で近い駅」であり、実際の徒歩経路とは異なります。徒歩時間まで考慮したい場合は、ルーティングエンジンや経路探索 API との組み合わせが必要になります。

## Overpass API 利用時に気をつけたこと

Overpass API は、OpenStreetMap のデータを柔軟に検索できる非常に便利な API です。
一方で、公開インスタンスは多くの利用者で共有されているため、アプリ側で負荷をかけすぎない設計にする必要があります。

今回のアプリでは、以下の点に気をつけました。

- 地図の移動やズームに連動して自動検索しない
- ユーザーが地点をクリックしたときだけ検索する
- 検索半径を最大 5,000m に制限する
- 取得件数を必要最小限にする
- Overpass QL に timeout を指定する
- フロントエンド側でも AbortController でタイムアウト制御する
- 検索中は連続実行しにくい UI にする
- エラー時は再試行を促すメッセージを表示する

Overpass API の制限は「1 秒あたり何リクエストまで」と単純に決まっているわけではなく、利用状況やクエリの重さに応じてスロットやクールダウンで制御される仕組みです。広範囲を対象にした重いクエリを繰り返すような使い方は避けるべきで、個人開発の MVP であっても「必要なときに、必要な範囲だけ問い合わせる」という意識は持っておきたいところです。

本格的に利用者が増える場合や、安定したレスポンスが必要な場合は、以下のような対応を検討した方がよさそうです。

- 独自の Overpass API インスタンスを立てる
- バックエンドを用意して結果をキャッシュする
- 検索対象エリアを限定して、駅データを事前取得する
- 静的な駅データセットを用意してアプリ側で検索する
- Overpass API に依存しない構成に切り替える

今回は、この中から **「静的な駅データセットを用意してアプリ側で検索する」** 方針を採用しました。

## 静的 JSON データへの移行

### なぜ方針転換したか

Overpass API のパブリックインスタンスは、サーバー負荷や同時利用数によって応答が遅くなることがあります。`[timeout:25]` を指定していても、実際にレスポンスが返ってこないケースが何度も発生しました。

「地図をクリックするたびに外部 API を呼び出す」設計では、API の安定性がそのまま利便性に直結します。どうせなら根本から解決しようと、「**全国の駅データを事前に一括取得し、静的 JSON ファイルとして配信する**」方式に切り替えました。

### 一括取得スクリプト

Python で日本国内（`ISO3166-1=JP`）の全鉄道駅を Overpass API から取得するスクリプトを作成しました。

```python
# tools/fetch-stations-from-osm.py（抜粋）
QUERY = """
[out:json][timeout:900];
area["ISO3166-1"="JP"][admin_level=2]->.japan;
(
  node["railway"="station"](area.japan);
  way["railway"="station"](area.japan);
);
out center tags;
""".strip()
```

バウンディングボックス方式ではなく `area` フィルタで日本の行政区域を指定することで、近隣国の駅の混入を防げます。実行すると **約 20 秒** で **8,669 駅** が取得でき、`public/data/stations.json`（約 1.07 MB）として保存されます。

```bash
pip install requests
python tools/fetch-stations-from-osm.py
# → ✅ 書き込み完了: 8669 駅 (1069.9 KB)
```

このスクリプトはデータ更新時（新駅開業・廃止時など）に実行します。アプリの実行時に Overpass API への呼び出しは一切ありません。

### アプリ側の実装

アプリ起動時に `stations.json` をフェッチしてメモリにキャッシュし、クリック時はキャッシュに対して Haversine 距離計算で近傍駅を絞り込みます。

```typescript
// src/services/staticStationService.ts（抜粋）
const BASE = (import.meta as any).env?.BASE_URL ?? '/'
const STATIONS_URL = `${BASE}data/stations.json`
let cachedStations: StaticStation[] | null = null

export async function loadStations(): Promise<StaticStation[]> {
  if (cachedStations) return cachedStations
  const res = await fetch(STATIONS_URL)
  if (!res.ok) throw new Error(`駅データの読み込みに失敗しました (${res.status})`)
  cachedStations = await res.json()
  return cachedStations!
}

export async function searchNearbyStations(
  lat: number, lon: number, radiusMeters: number,
): Promise<Station[]> {
  const all = await loadStations()
  return all
    .map((s) => ({ ...s, distanceMeters: haversineDistance(lat, lon, s.lat, s.lon) }))
    .filter((s) => s.distanceMeters <= radiusMeters)
    .sort((a, b) => a.distanceMeters - b.distanceMeters)
    .slice(0, 10)
}
```

これにともない、検索のレスポンスが常に安定し、タイムアウトエラーがゼロになりました。

### 静的データ化のトレードオフ

| 観点 | Overpass API（リアルタイム） | 静的 JSON |
|---|---|---|
| 安定性 | ❌ タイムアウト・遅延が発生 | ✅ 常に高速・安定 |
| データ鮮度 | ✅ 常に最新 | ⚠️ 更新時に再取得が必要 |
| 初回ロード | ✅ 軽い（必要な分だけ） | ⚠️ 約 1 MB のダウンロード |
| 外部依存 | ❌ API の稼働に依存 | ✅ 静的ファイル配信のみ |

駅の廃止・開業は頻繁ではないため、多少のデータの古さは許容できます。初回の約 1 MB ダウンロードも、ブラウザのキャッシュが効けば 2 回目以降は発生しません。

## タイムアウトは AbortController で制御（初期実装）

:::message
この実装は Overpass API をリアルタイムで呼び出す初期設計のものです。現在は静的 JSON を使用しているため実行時には不要になりましたが、外部 API 呼び出し全般に応用できる実装パターンとして残しています。
:::

```typescript
const controller = new AbortController()
const timeoutId = setTimeout(() => controller.abort(), 30000)

try {
  const response = await fetch(OVERPASS_URL, {
    method: 'POST',
    signal: controller.signal,
    // ...
  })
} catch (err) {
  if (err instanceof Error && err.name === 'AbortError') {
    throw new Error('検索がタイムアウトしました。しばらく後に再度お試しください。')
  }
  throw err
} finally {
  clearTimeout(timeoutId)
}
```

## テストは Vitest で

地理計算と Overpass クエリ生成については Vitest でユニットテストを書いています。Haversine 計算の精度検証、距離フォーマット（「約1.2km」など）の表示確認、重複排除ロジックのテスト、静的駅データサービス（`staticStationService`）のテストなど、計42件が通っています。

```bash
npm run test:run
# → 42 passed in 269ms
```

## モバイル対応で気をつけたこと

スマートフォン（iPhone 13 Pro、390×844px 基準）での使い勝手を後から改善しました。やってみて「これは必要だった」と思った点を挙げます。

**タップターゲットのサイズ**
Apple の Human Interface Guidelines では、タップ可能な要素は最小 44×44px 推奨とされています。ボタンやセレクトボックスに `min-height: 44px` を設定するだけで体感がかなり変わります。

**iOS の 300ms タップ遅延**
古い Safari にはダブルタップズームのための 300ms 遅延があります。`touch-action: manipulation` を設定すると解消されます。

```css
button, select, a {
  touch-action: manipulation;
}
```

**Safe Area（ノッチ・ホームバー）対応**
iPhone X 以降のホームインジケーター部分と重ならないよう、`env(safe-area-inset-bottom)` で余白を確保しています。`viewport-fit=cover` とセットで使います。

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
```

```css
padding-bottom: max(12px, env(safe-area-inset-bottom));
```

## GitHub Actions で自動デプロイ

`main` ブランチにプッシュすると、型チェック → テスト → ビルド → GitHub Pages デプロイが自動で走ります。

```yaml
jobs:
  build:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '24'
          cache: 'npm'
      - run: npm ci
      - run: npm run type-check
      - run: npm run test:run    # ウォッチモードではなく1回実行
      - run: npm run build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist
```

一点ハマりポイントとして、GitHub Pages はサブパス（`https://ユーザー名.github.io/リポジトリ名/`）でホストされるため、`vite.config.ts` の `base` をリポジトリ名に合わせる必要があります。これを忘れると CSS や JS の参照パスがズレて真っ白な画面になります。

```typescript
// vite.config.ts
export default defineConfig({
  base: '/nearest-station-map/',  // ← これが必要
})
```

# まとめ

最初は Overpass API をリアルタイムで呼び出す設計でスタートしましたが、タイムアウトの頻発という壁にぶつかりました。「全国駅データを事前取得 → 静的 JSON として配信 → クライアント側で距離計算」という方式に切り替えたことで、外部 API への依存をなくしたことで安定した操作性を実現できました。

データの鮮度とのトレードオフはありますが、駅の廃止・開業の頻度を考えれば定期的な再取得で十分対応できます。同じような外部 API の安定性問題で悩んでいる方の参考になれば嬉しいです。

ソースコードは GitHub へ公開しています。

https://github.com/yutaka-art/nearest-station-map

フィードバックや「こういう機能も欲しい」などあれば、GitHub の Issue や X（旧Twitter）でお気軽にどうぞ。

# 参考リンク
https://operations.osmfoundation.org/policies/tiles/
https://osmfoundation.org/wiki/Licence/Attribution_Guidelines
https://wiki.openstreetmap.org/wiki/Overpass_API
https://dev.overpass-api.de/overpass-doc/en/preface/commons.html
https://operations.osmfoundation.org/policies/nominatim/
https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action
https://developer.mozilla.org/en-US/docs/Web/CSS/env
https://vite.dev/guide/static-deploy.html
https://docs.github.com/en/pages
