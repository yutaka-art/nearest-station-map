import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { loadStations, searchNearbyStations, clearStationCache } from './staticStationService'
import type { StaticStation } from '../types/station'

// ─── テスト用フィクスチャ ──────────────────────────────────
const TOKYO: StaticStation = {
  id: 'n05-000001',
  name: '東京',
  lat: 35.681236,
  lon: 139.767125,
  operator: '東日本旅客鉄道',
  line: '東海道線',
  source: '国土数値情報 鉄道時系列データ',
}

const SHINJUKU: StaticStation = {
  id: 'n05-000002',
  name: '新宿',
  lat: 35.689592,
  lon: 139.700413,
  operator: '東日本旅客鉄道',
  line: '中央線',
  source: '国土数値情報 鉄道時系列データ',
}

const SAPPORO: StaticStation = {
  id: 'n05-000003',
  name: '札幌',
  lat: 43.068661,
  lon: 141.350755,
  operator: '北海道旅客鉄道',
  line: '函館本線',
  source: '国土数値情報 鉄道時系列データ',
}

// ─── fetch モック ─────────────────────────────────────────
function mockFetch(data: unknown, ok = true, status = 200) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(data),
  } as Response))
}

describe('loadStations', () => {
  beforeEach(() => {
    clearStationCache()
    vi.restoreAllMocks()
  })

  afterEach(() => {
    clearStationCache()
  })

  it('stations.json を正常に読み込める', async () => {
    mockFetch([TOKYO, SHINJUKU])
    const result = await loadStations()
    expect(result).toHaveLength(2)
    expect(result[0].name).toBe('東京')
  })

  it('2回目の呼び出しはキャッシュを返す（fetch は1回だけ）', async () => {
    mockFetch([TOKYO])
    await loadStations()
    await loadStations()
    expect(vi.mocked(globalThis.fetch)).toHaveBeenCalledTimes(1)
  })

  it('HTTP エラー時に例外をスローする', async () => {
    mockFetch(null, false, 404)
    await expect(loadStations()).rejects.toThrow('HTTP 404')
  })

  it('レスポンスが配列でない場合に例外をスローする', async () => {
    mockFetch({ error: 'invalid' })
    await expect(loadStations()).rejects.toThrow('形式が不正')
  })
})

describe('searchNearbyStations', () => {
  beforeEach(() => {
    clearStationCache()
    vi.restoreAllMocks()
  })

  afterEach(() => {
    clearStationCache()
  })

  it('検索半径内の駅だけを返す', async () => {
    mockFetch([TOKYO, SHINJUKU, SAPPORO])
    // 東京駅付近から半径 1000m: 東京駅のみ
    const result = await searchNearbyStations(35.681236, 139.767125, 1000)
    expect(result.map((s) => s.name)).toContain('東京')
    expect(result.map((s) => s.name)).not.toContain('札幌')
  })

  it('距離が近い順にソートされている', async () => {
    mockFetch([SAPPORO, SHINJUKU, TOKYO])
    // 東京駅付近から検索
    const result = await searchNearbyStations(35.681236, 139.767125, 100000)
    expect(result[0].name).toBe('東京')
    expect(result[1].name).toBe('新宿')
  })

  it('最大 10 件に制限される', async () => {
    const many: StaticStation[] = Array.from({ length: 20 }, (_, i) => ({
      id: `n05-${i}`,
      name: `駅${i}`,
      lat: 35.681236 + i * 0.0001,
      lon: 139.767125 + i * 0.0001,
      source: 'テスト',
    }))
    mockFetch(many)
    const result = await searchNearbyStations(35.681236, 139.767125, 100000)
    expect(result).toHaveLength(10)
  })

  it('distanceMeters が正しく設定されている', async () => {
    mockFetch([TOKYO])
    const result = await searchNearbyStations(35.681236, 139.767125, 1000)
    expect(result[0].distanceMeters).toBe(0)
  })

  it('operator・line が Station に引き継がれる', async () => {
    mockFetch([TOKYO])
    const result = await searchNearbyStations(35.681236, 139.767125, 1000)
    expect(result[0].operator).toBe('東日本旅客鉄道')
    expect(result[0].line).toBe('東海道線')
  })

  it('operator が null の場合は undefined になる', async () => {
    const noOp: StaticStation = { ...TOKYO, operator: null }
    mockFetch([noOp])
    const result = await searchNearbyStations(35.681236, 139.767125, 1000)
    expect(result[0].operator).toBeUndefined()
  })

  it('JSON 読み込み失敗時に例外をスローする', async () => {
    mockFetch(null, false, 500)
    await expect(
      searchNearbyStations(35.681236, 139.767125, 1000),
    ).rejects.toThrow()
  })
})
