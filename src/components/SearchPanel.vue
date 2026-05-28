<template>
  <div class="search-panel">
    <!-- モバイルで横並び: 検索半径 + 現在地ボタン -->
    <div class="controls-row">
      <div class="panel-section radius-section">
        <label for="radius-select" class="label">検索半径</label>
        <select
          id="radius-select"
          :value="radiusMeters"
          :disabled="isLoading"
          class="select"
          @change="onRadiusChange"
        >
          <option value="1000">1,000 m</option>
          <option value="2000">2,000 m</option>
          <option value="3000">3,000 m</option>
          <option value="5000">5,000 m</option>
        </select>
      </div>

      <div class="panel-section geo-section">
        <button
          class="btn btn-geo"
          :disabled="isLoading"
          @click="onGeolocate"
        >
          📍 現在地から探す
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="status loading" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span>
      検索中...
    </div>

    <div v-if="hint && !isLoading" class="status hint" role="status" aria-live="polite">
      {{ hint }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  radiusMeters: number
  isLoading: boolean
  hasClickedPoint: boolean
}>()

const emit = defineEmits<{
  'update:radiusMeters': [value: number]
  geolocate: []
}>()

const hint = computed(() => {
  if (!props.hasClickedPoint) return '地図をクリックして検索地点を指定してください'
  return null
})

function onRadiusChange(event: Event): void {
  const value = Number((event.target as HTMLSelectElement).value)
  emit('update:radiusMeters', value)
}

function onGeolocate(): void {
  emit('geolocate')
}
</script>

<style scoped>
.search-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.controls-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 0.85rem;
  color: #555;
  font-weight: 600;
}

.select {
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.95rem;
  background: #fff;
  cursor: pointer;
  /* iOS デフォルトスタイルをリセット */
  -webkit-appearance: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23666' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}

.select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn {
  padding: 10px 14px;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.15s;
  /* タップフィードバック */
  -webkit-tap-highlight-color: transparent;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-geo {
  background: #27ae60;
  color: #fff;
}

.btn-geo:not(:disabled):active {
  background: #1e8449;
}

.btn-geo:not(:disabled):hover {
  background: #219a52;
}

.status {
  font-size: 0.88rem;
  padding: 8px 10px;
  border-radius: 6px;
}

.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #eaf4fb;
  color: #2980b9;
}

.hint {
  background: #fef9e7;
  color: #856404;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #2980b9;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* モバイル: 検索半径とボタンを横並び */
@media (max-width: 768px) {
  .search-panel {
    gap: 8px;
  }

  .controls-row {
    flex-direction: row;
    align-items: flex-end;
    gap: 8px;
  }

  .radius-section {
    flex: 1;
  }

  .geo-section {
    flex-shrink: 0;
  }

  /* 44px 以上のタップターゲット */
  .select,
  .btn {
    min-height: 44px;
    font-size: 1rem;
  }

  .btn-geo {
    padding: 0 16px;
    white-space: nowrap;
  }
}
</style>
