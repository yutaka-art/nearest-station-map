export type Station = {
  id: string
  name: string
  lat: number
  lon: number
  distanceMeters: number
  tags: Record<string, string>
  osmType: 'node' | 'way' | 'relation'
  osmId: number
}

export type SearchParams = {
  lat: number
  lon: number
  radiusMeters: number
}
