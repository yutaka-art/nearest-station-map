<template>
  <div class="station-list">
    <h2 class="list-title">検索結果</h2>

    <div aria-live="polite" aria-atomic="true">
      <div v-if="errorMessage" class="error-message" role="alert">
        <span class="error-icon">⚠️</span>
        {{ errorMessage }}
      </div>

      <template v-else-if="stations.length > 0">
        <p class="result-count">{{ stations.length }} 件見つかりました</p>
        <ul class="list">
          <li
            v-for="(station, index) in stations"
            :key="station.id"
            class="station-item"
          >
            <div class="station-rank">{{ index + 1 }}</div>
            <div class="station-info">
              <div class="station-name">{{ station.name }}</div>
              <div class="station-meta">
                <span class="station-distance">{{ formatDistance(station.distanceMeters) }}</span>
                <span class="station-type">{{ getStationMeta(station) }}</span>
              </div>
            </div>
            <button
              class="btn-view"
              title="地図で見る"
              @click="emit('flyTo', station)"
            >
              地図で見る
            </button>
          </li>
        </ul>
      </template>

      <div v-else-if="!isLoading && hasSearched" class="empty-message">
        駅が見つかりませんでした。
      </div>

      <div v-else-if="!hasSearched" class="empty-message placeholder">
        地図をクリックすると近くの駅を検索します。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Station } from '../types/station'
import { formatDistance } from '../utils/geo'

defineProps<{
  stations: Station[]
  isLoading: boolean
  errorMessage: string | null
  hasSearched: boolean
}>()

const emit = defineEmits<{
  flyTo: [station: Station]
}>()

function getStationMeta(station: Station): string {
  const parts: string[] = []
  if (station.line) parts.push(station.line)
  if (station.operator) parts.push(station.operator)
  return parts.join(' / ')
}
</script>

<style scoped>
.station-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-title {
  font-size: 1rem;
  font-weight: 700;
  margin: 0;
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 6px;
}

.result-count {
  font-size: 0.82rem;
  color: #666;
  margin: 0;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.station-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: background 0.1s;
  /* 最小タップターゲット */
  min-height: 52px;
  -webkit-tap-highlight-color: transparent;
}

.station-item:hover {
  background: #eaf4fb;
}

.station-rank {
  width: 28px;
  height: 28px;
  min-width: 28px;
  background: #2980b9;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  font-weight: 700;
}

.station-info {
  flex: 1;
  min-width: 0;
}

.station-name {
  font-weight: 600;
  font-size: 0.95rem;
  color: #2c3e50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.station-meta {
  display: flex;
  gap: 8px;
  margin-top: 2px;
  flex-wrap: wrap;
}

.station-distance {
  font-size: 0.82rem;
  color: #e74c3c;
  font-weight: 600;
}

.station-type {
  font-size: 0.78rem;
  color: #888;
  background: #e9ecef;
  padding: 1px 6px;
  border-radius: 4px;
}

.btn-view {
  padding: 5px 10px;
  font-size: 0.78rem;
  background: #3498db;
  color: #fff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
  /* 最小タップターゲット */
  min-height: 36px;
  min-width: 72px;
  -webkit-tap-highlight-color: transparent;
}

.btn-view:active {
  background: #1a6fa8;
}

.btn-view:hover {
  background: #2980b9;
}

.error-message {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  background: #fdf2f2;
  color: #c0392b;
  border: 1px solid #f5c6cb;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 0.9rem;
}

.error-icon {
  flex-shrink: 0;
}

.empty-message {
  font-size: 0.88rem;
  color: #888;
  text-align: center;
  padding: 20px 0;
}

.placeholder {
  color: #aaa;
}

/* モバイル: タップターゲットをさらに拡大 */
@media (max-width: 768px) {
  .station-item {
    padding: 12px;
    gap: 12px;
  }

  .station-rank {
    width: 32px;
    height: 32px;
    min-width: 32px;
    font-size: 0.9rem;
  }

  .station-name {
    font-size: 1rem;
  }

  .station-distance {
    font-size: 0.88rem;
  }

  .btn-view {
    min-height: 44px;
    min-width: 80px;
    font-size: 0.85rem;
    padding: 0 12px;
  }
}
</style>
