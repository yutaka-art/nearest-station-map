export type Station = {
  id: string
  name: string
  lat: number
  lon: number
  distanceMeters: number
  operator?: string
  line?: string
  source?: string
}

export type StaticStation = {
  id: string
  name: string
  lat: number
  lon: number
  operator?: string | null
  line?: string | null
  source: string
}

export type SearchParams = {
  lat: number
  lon: number
  radiusMeters: number
}
