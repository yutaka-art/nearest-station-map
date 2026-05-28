import { describe, it, expect } from 'vitest'
import { buildOverpassQuery, deduplicateStations } from './overpassService'
import type { Station } from '../types/station'

describe('buildOverpassQuery', () => {
  it('Overpass QL 文字列に座標と半径が含まれる', () => {
    const query = buildOverpassQuery(35.6812, 139.7671, 3000)
    expect(query).toContain('35.6812')
    expect(query).toContain('139.7671')
    expect(query).toContain('3000')
  })

  it('[out:json] と [timeout:25] が含まれる', () => {
    const query = buildOverpassQuery(35.0, 135.0, 1000)
    expect(query).toContain('[out:json]')
    expect(query).toContain('[timeout:25]')
  })

  it('railway と public_transport の両方のフィルターが含まれる', () => {
    const query = buildOverpassQuery(35.0, 135.0, 1000)
    expect(query).toContain('"railway"')
    expect(query).toContain('"public_transport"')
  })

  it('"name" フィルターが含まれる（無名駅を除外）', () => {
    const query = buildOverpassQuery(35.0, 135.0, 1000)
    expect(query).toContain('"name"')
  })

  it('out center tags が含まれる（way/relation の座標取得用）', () => {
    const query = buildOverpassQuery(35.0, 135.0, 1000)
    expect(query).toContain('out center tags')
  })
})

const makeStation = (overrides: { name: string; lat: number; lon: number; distanceMeters: number } & Partial<Station>): Station => ({
  id: `node/${Math.random()}`,
  ...overrides,
})

describe('deduplicateStations', () => {
  it('重複なしの場合はそのまま返す', () => {
    const stations = [
      makeStation({ name: '東京駅', lat: 35.6812, lon: 139.7671, distanceMeters: 100 }),
      makeStation({ name: '新宿駅', lat: 35.6896, lon: 139.7006, distanceMeters: 500 }),
    ]
    expect(deduplicateStations(stations)).toHaveLength(2)
  })

  it('同名かつ座標差 0.001° 未満の重複は短い方だけ残す', () => {
    const closer = makeStation({ name: '渋谷駅', lat: 35.6580, lon: 139.7016, distanceMeters: 200 })
    const farther = makeStation({ name: '渋谷駅', lat: 35.6582, lon: 139.7017, distanceMeters: 300 })
    const result = deduplicateStations([closer, farther])
    expect(result).toHaveLength(1)
    expect(result[0].distanceMeters).toBe(200)
  })

  it('同名でも座標差が 0.001° 以上なら重複として扱わない', () => {
    const s1 = makeStation({ name: '横浜駅', lat: 35.4660, lon: 139.6222, distanceMeters: 1000 })
    const s2 = makeStation({ name: '横浜駅', lat: 35.4750, lon: 139.6320, distanceMeters: 1500 }) // 差 > 0.001
    const result = deduplicateStations([s1, s2])
    expect(result).toHaveLength(2)
  })

  it('名前が異なれば座標が近くても重複として扱わない', () => {
    const s1 = makeStation({ name: '品川駅', lat: 35.6286, lon: 139.7387, distanceMeters: 100 })
    const s2 = makeStation({ name: '北品川駅', lat: 35.6287, lon: 139.7388, distanceMeters: 150 })
    const result = deduplicateStations([s1, s2])
    expect(result).toHaveLength(2)
  })

  it('空配列を渡した場合は空配列を返す', () => {
    expect(deduplicateStations([])).toEqual([])
  })

  it('重複が複数ある場合、最も距離が短いものを残す', () => {
    const a = makeStation({ name: '池袋駅', lat: 35.7295, lon: 139.7109, distanceMeters: 500 })
    const b = makeStation({ name: '池袋駅', lat: 35.7296, lon: 139.7110, distanceMeters: 200 })
    const c = makeStation({ name: '池袋駅', lat: 35.7294, lon: 139.7108, distanceMeters: 350 })
    const result = deduplicateStations([a, b, c])
    expect(result).toHaveLength(1)
    expect(result[0].distanceMeters).toBe(200)
  })
})
