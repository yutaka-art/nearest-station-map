import type { Station } from '../types/station'
import { haversineDistance } from '../utils/geo'

const OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

type OverpassElement = {
  type: 'node' | 'way' | 'relation'
  id: number
  lat?: number
  lon?: number
  center?: { lat: number; lon: number }
  tags?: Record<string, string>
}

type OverpassResponse = {
  elements: OverpassElement[]
}

/**
 * Overpass QL クエリを生成する
 */
export function buildOverpassQuery(
  lat: number,
  lon: number,
  radiusMeters: number,
): string {
  const around = `around:${radiusMeters},${lat},${lon}`
  return `[out:json][timeout:25];
(
  node["railway"~"station|halt"]["name"](${around});
  way["railway"~"station|halt"]["name"](${around});
  relation["railway"~"station|halt"]["name"](${around});
  node["public_transport"="station"]["name"](${around});
  way["public_transport"="station"]["name"](${around});
  relation["public_transport"="station"]["name"](${around});
);
out center tags;`
}

/**
 * Overpass API から駅データを取得し、Station[] に変換して返す
 * クライアント側 30 秒タイムアウトを AbortController で実装する (FR-021)
 */
export async function fetchNearestStations(
  lat: number,
  lon: number,
  radiusMeters: number,
): Promise<Station[]> {
  const query = buildOverpassQuery(lat, lon, radiusMeters)

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000)

  let response: Response
  try {
    response = await fetch(OVERPASS_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      },
      body: new URLSearchParams({ data: query }),
      signal: controller.signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('検索がタイムアウトしました。しばらく後に再度お試しください。')
    }
    throw err
  } finally {
    clearTimeout(timeoutId)
  }

  if (!response.ok) {
    throw new Error(
      `Overpass API エラー: ${response.status} ${response.statusText}`,
    )
  }

  const data: OverpassResponse = await response.json()

  const stations: Station[] = data.elements
    .map((el) => {
      const stLat = el.lat ?? el.center?.lat
      const stLon = el.lon ?? el.center?.lon
      if (stLat === undefined || stLon === undefined) return null

      const tags = el.tags ?? {}
      const name = tags['name']
      if (!name) return null

      const distance = haversineDistance(lat, lon, stLat, stLon)

      return {
        id: `${el.type}/${el.id}`,
        name,
        lat: stLat,
        lon: stLon,
        distanceMeters: distance,
        tags,
        osmType: el.type,
        osmId: el.id,
      } satisfies Station
    })
    .filter((s): s is Station => s !== null)

  return deduplicateStations(stations)
}

/**
 * 同名かつ座標が近い重複データを除外する (距離が短い方を残す)
 */
export function deduplicateStations(stations: Station[]): Station[] {
  const COORD_THRESHOLD = 0.001 // 約100m 程度
  const result: Station[] = []

  for (const station of stations) {
    const duplicate = result.find(
      (s) =>
        s.name === station.name &&
        Math.abs(s.lat - station.lat) < COORD_THRESHOLD &&
        Math.abs(s.lon - station.lon) < COORD_THRESHOLD,
    )
    if (duplicate) {
      if (station.distanceMeters < duplicate.distanceMeters) {
        const idx = result.indexOf(duplicate)
        result[idx] = station
      }
    } else {
      result.push(station)
    }
  }

  return result
}
