import { ref } from 'vue'
import type { Station, SearchParams } from '../types/station'
import { searchNearbyStations } from '../services/staticStationService'
import { isValidCoordinate } from '../utils/geo'

export function useNearestStations() {
  const stations = ref<Station[]>([])
  const isLoading = ref(false)
  const errorMessage = ref<string | null>(null)
  const searchedParams = ref<SearchParams | null>(null)

  async function search(params: SearchParams): Promise<void> {
    const { lat, lon, radiusMeters } = params

    if (!isValidCoordinate(lat, lon)) {
      errorMessage.value = '緯度・経度の値が不正です。'
      return
    }

    isLoading.value = true
    errorMessage.value = null
    stations.value = []

    try {
      const results = await searchNearbyStations(lat, lon, radiusMeters)
      stations.value = results
      searchedParams.value = params

      if (results.length === 0) {
        errorMessage.value = `半径 ${radiusMeters}m 以内に駅が見つかりませんでした。`
      }
    } catch (err) {
      if (err instanceof Error) {
        errorMessage.value = `検索に失敗しました: ${err.message}`
      } else {
        errorMessage.value = '予期しないエラーが発生しました。'
      }
      stations.value = []
    } finally {
      isLoading.value = false
    }
  }

  function clearResults(): void {
    stations.value = []
    errorMessage.value = null
    searchedParams.value = null
  }

  return {
    stations,
    isLoading,
    errorMessage,
    searchedParams,
    search,
    clearResults,
  }
}
