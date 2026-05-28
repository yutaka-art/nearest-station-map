import type { Station, StaticStation } from '../types/station'
import { haversineDistance } from '../utils/geo'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const BASE = (import.meta as any).env?.BASE_URL ?? '/'
const STATIONS_URL = `${BASE}data/stations.json`
const MAX_RESULTS = 10

let cachedStations: StaticStation[] | null = null

/**
 * stations.json を読み込む（初回のみ fetch、以降はキャッシュを返す）
 */
export async function loadStations(): Promise<StaticStation[]> {
  if (cachedStations !== null) return cachedStations

  const response = await fetch(STATIONS_URL)
  if (!response.ok) {
    throw new Error(
      `駅データの読み込みに失敗しました (HTTP ${response.status})。`,
    )
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data)) {
    throw new Error('駅データの形式が不正です。')
  }

  cachedStations = data as StaticStation[]
  return cachedStations
}

/**
 * 指定地点から検索半径内の駅を距離順で最大 MAX_RESULTS 件返す
 */
export async function searchNearbyStations(
  lat: number,
  lon: number,
  radiusMeters: number,
): Promise<Station[]> {
  const all = await loadStations()

  const results: Station[] = []

  for (const st of all) {
    const distance = haversineDistance(lat, lon, st.lat, st.lon)
    if (distance <= radiusMeters) {
      results.push({
        id: st.id,
        name: st.name,
        lat: st.lat,
        lon: st.lon,
        distanceMeters: distance,
        operator: st.operator ?? undefined,
        line: st.line ?? undefined,
        source: st.source,
      })
    }
  }

  return results
    .sort((a, b) => a.distanceMeters - b.distanceMeters)
    .slice(0, MAX_RESULTS)
}

/**
 * キャッシュをクリアする（テスト用）
 */
export function clearStationCache(): void {
  cachedStations = null
}
