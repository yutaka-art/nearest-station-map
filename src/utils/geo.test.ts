import { describe, it, expect } from 'vitest'
import { haversineDistance, formatDistance, isValidCoordinate } from './geo'

describe('haversineDistance', () => {
  it('同一地点間の距離は 0 を返す', () => {
    expect(haversineDistance(35.681236, 139.767125, 35.681236, 139.767125)).toBe(0)
  })

  it('東京駅 → 新宿駅は約 6.4 km', () => {
    // 東京駅: 35.6812, 139.7671 / 新宿駅: 35.6896, 139.7006
    const dist = haversineDistance(35.6812, 139.7671, 35.6896, 139.7006)
    expect(dist).toBeGreaterThan(6000)
    expect(dist).toBeLessThan(7000)
  })

  it('赤道上の 1 度差は約 111 km', () => {
    const dist = haversineDistance(0, 0, 0, 1)
    expect(dist).toBeGreaterThan(110000)
    expect(dist).toBeLessThan(112000)
  })

  it('南極から北極は約 20015 km', () => {
    const dist = haversineDistance(-90, 0, 90, 0)
    expect(dist).toBeGreaterThan(20000000)
    expect(dist).toBeLessThan(20100000)
  })
})

describe('formatDistance', () => {
  it('999m は "999 m" を返す', () => {
    expect(formatDistance(999)).toBe('999 m')
  })

  it('1000m は "1.0 km" を返す', () => {
    expect(formatDistance(1000)).toBe('1.0 km')
  })

  it('1500m は "1.5 km" を返す', () => {
    expect(formatDistance(1500)).toBe('1.5 km')
  })

  it('0m は "0 m" を返す', () => {
    expect(formatDistance(0)).toBe('0 m')
  })

  it('小数点以下は四捨五入される (499.4 → "499 m")', () => {
    expect(formatDistance(499.4)).toBe('499 m')
  })

  it('10000m は "10.0 km" を返す', () => {
    expect(formatDistance(10000)).toBe('10.0 km')
  })
})

describe('isValidCoordinate', () => {
  it('有効な座標（東京）は true を返す', () => {
    expect(isValidCoordinate(35.6812, 139.7671)).toBe(true)
  })

  it('緯度 90 は有効', () => {
    expect(isValidCoordinate(90, 0)).toBe(true)
  })

  it('緯度 -90 は有効', () => {
    expect(isValidCoordinate(-90, 0)).toBe(true)
  })

  it('経度 180 は有効', () => {
    expect(isValidCoordinate(0, 180)).toBe(true)
  })

  it('経度 -180 は有効', () => {
    expect(isValidCoordinate(0, -180)).toBe(true)
  })

  it('緯度 91 は無効', () => {
    expect(isValidCoordinate(91, 0)).toBe(false)
  })

  it('緯度 -91 は無効', () => {
    expect(isValidCoordinate(-91, 0)).toBe(false)
  })

  it('経度 181 は無効', () => {
    expect(isValidCoordinate(0, 181)).toBe(false)
  })

  it('経度 -181 は無効', () => {
    expect(isValidCoordinate(0, -181)).toBe(false)
  })

  it('NaN は無効', () => {
    expect(isValidCoordinate(NaN, 0)).toBe(false)
    expect(isValidCoordinate(0, NaN)).toBe(false)
  })
})
