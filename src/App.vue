<template>
  <div class="app">
    <header class="header">
      <div class="header-inner">
        <h1 class="app-title">Nearest Station Map</h1>
        <p class="app-desc">地図をクリックすると、その地点周辺の駅を距離順に表示します。</p>
      </div>
    </header>

    <main class="main">
      <div class="map-area">
        <MapView
          ref="mapViewRef"
          :stations="stations"
          :is-searching="isLoading"
          @map-click="onMapClick"
        />
      </div>

      <aside class="side-panel">
        <SearchPanel
          v-model:radius-meters="radiusMeters"
          :is-loading="isLoading"
          :has-clicked-point="hasClickedPoint"
          @geolocate="onGeolocate"
        />

        <div v-if="geoError" class="geo-error" role="alert">
          <span>⚠️ {{ geoError }}</span>
        </div>

        <StationList
          :stations="stations"
          :is-loading="isLoading"
          :error-message="errorMessage"
          :has-searched="hasSearched"
          @fly-to="onFlyTo"
        />
      </aside>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MapView from './components/MapView.vue'
import SearchPanel from './components/SearchPanel.vue'
import StationList from './components/StationList.vue'
import { useNearestStations } from './composables/useNearestStations'
import type { Station } from './types/station'

const mapViewRef = ref<InstanceType<typeof MapView> | null>(null)
const radiusMeters = ref(3000)
const hasClickedPoint = ref(false)
const hasSearched = ref(false)
const geoError = ref<string | null>(null)

const { stations, isLoading, errorMessage, search } = useNearestStations()

async function onMapClick(lat: number, lon: number): Promise<void> {
  if (isLoading.value) return
  hasClickedPoint.value = true
  hasSearched.value = true
  geoError.value = null
  await search({ lat, lon, radiusMeters: radiusMeters.value })
}

function onGeolocate(): void {
  if (isLoading.value) return
  if (!navigator.geolocation) {
    geoError.value = 'このブラウザは位置情報に対応していません。'
    return
  }
  geoError.value = null
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const { latitude: lat, longitude: lon } = position.coords
      hasClickedPoint.value = true
      hasSearched.value = true
      mapViewRef.value?.panTo(lat, lon)
      await search({ lat, lon, radiusMeters: radiusMeters.value })
    },
    (err) => {
      switch (err.code) {
        case err.PERMISSION_DENIED:
          geoError.value = '位置情報へのアクセスが拒否されました。'
          break
        case err.POSITION_UNAVAILABLE:
          geoError.value = '位置情報を取得できませんでした。'
          break
        case err.TIMEOUT:
          geoError.value = '位置情報の取得がタイムアウトしました。'
          break
        default:
          geoError.value = '位置情報の取得中にエラーが発生しました。'
      }
    },
    { timeout: 10000 },
  )
}

function onFlyTo(station: Station): void {
  mapViewRef.value?.flyToStation(station)
}
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  min-height: 100vh;
}

.header {
  background: #2c3e50;
  color: #fff;
  padding: 10px 16px;
  flex-shrink: 0;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
}

.app-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.app-desc {
  margin: 2px 0 0;
  font-size: 0.82rem;
  opacity: 0.8;
}

.main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.map-area {
  flex: 1;
  overflow: hidden;
}

.side-panel {
  width: 320px;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border-left: 1px solid #e9ecef;
  overflow-y: auto;
}

.geo-error {
  background: #fdf2f2;
  color: #c0392b;
  border: 1px solid #f5c6cb;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.88rem;
}

/* スマートフォン: 縦並び */
@media (max-width: 768px) {
  .header {
    padding: 6px 16px 6px max(16px, env(safe-area-inset-left));
  }

  .app-title {
    font-size: 1rem;
  }

  .app-desc {
    display: none;
  }

  .main {
    flex-direction: column;
  }

  .map-area {
    height: 45vh;
    flex: none;
  }

  .side-panel {
    width: 100%;
    min-width: 0;
    border-left: none;
    border-top: 1px solid #e9ecef;
    max-height: 55vh;
    overflow-y: auto;
    gap: 10px;
    padding: 12px 16px;
    /* iPhone ホームバー（Safe Area）分の余白 */
    padding-bottom: max(12px, env(safe-area-inset-bottom));
    /* iOS 慣性スクロール */
    -webkit-overflow-scrolling: touch;
  }
}
</style>
