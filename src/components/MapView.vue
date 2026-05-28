<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import OSM from 'ol/source/OSM'
import { defaults as defaultControls } from 'ol/control'
import Attribution from 'ol/control/Attribution'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import { fromLonLat, toLonLat } from 'ol/proj'
import { Style, Fill, Stroke, Circle as CircleStyle, Text } from 'ol/style'
import Overlay from 'ol/Overlay'
import type { Coordinate } from 'ol/coordinate'
import type { Station } from '../types/station'
import { formatDistance } from '../utils/geo'

const props = defineProps<{
  stations: Station[]
  isSearching: boolean
}>()

const emit = defineEmits<{
  mapClick: [lat: number, lon: number]
}>()

const mapContainer = ref<HTMLDivElement | null>(null)

let map: Map | null = null
let clickMarkerSource: VectorSource | null = null
let stationSource: VectorSource | null = null
let popup: Overlay | null = null
let popupElement: HTMLDivElement | null = null

const TOKYO_STATION = fromLonLat([139.767125, 35.681236])

function createClickMarkerStyle(): Style {
  return new Style({
    image: new CircleStyle({
      radius: 10,
      fill: new Fill({ color: '#e74c3c' }),
      stroke: new Stroke({ color: '#ffffff', width: 2 }),
    }),
  })
}

function createStationStyle(rank: number): Style {
  return new Style({
    image: new CircleStyle({
      radius: 14,
      fill: new Fill({ color: '#2980b9' }),
      stroke: new Stroke({ color: '#ffffff', width: 2 }),
    }),
    text: new Text({
      text: String(rank),
      fill: new Fill({ color: '#ffffff' }),
      font: 'bold 11px sans-serif',
    }),
  })
}

function initMap(): void {
  if (!mapContainer.value) return

  clickMarkerSource = new VectorSource()
  stationSource = new VectorSource()

  popupElement = document.createElement('div')
  popupElement.className = 'map-popup'
  popupElement.style.display = 'none'

  popup = new Overlay({
    element: popupElement,
    positioning: 'bottom-center',
    stopEvent: false,
    offset: [0, -16],
  })

  map = new Map({
    target: mapContainer.value,
    controls: defaultControls({ attribution: false }).extend([
      new Attribution({
        collapsible: true,
        collapsed: window.innerWidth <= 768,
      }),
    ]),
    layers: [
      new TileLayer({ source: new OSM() }),
      new VectorLayer({ source: stationSource }),
      new VectorLayer({ source: clickMarkerSource }),
    ],
    overlays: [popup],
    view: new View({
      center: TOKYO_STATION,
      zoom: 14,
    }),
  })

  map.on('click', (evt) => {
    if (props.isSearching) return

    // ポップアップを閉じる
    if (popupElement) popupElement.style.display = 'none'

    // 駅マーカークリックチェック
    const feature = map!.forEachFeatureAtPixel(evt.pixel, (f) => f)
    if (feature) {
      const stationType = feature.get('type') as string | undefined
      if (stationType === 'station') {
        const name = feature.get('name') as string
        const distance = feature.get('distance') as number
        if (popupElement && popup) {
          popupElement.innerHTML = `<strong>${name}</strong><br>${formatDistance(distance)}`
          popupElement.style.display = 'block'
          popup.setPosition(
            (feature.getGeometry() as Point).getCoordinates() as Coordinate,
          )
        }
        return
      }
    }

    const coord = toLonLat(evt.coordinate)
    const [lon, lat] = coord
    updateClickMarker(evt.coordinate)
    emit('mapClick', lat, lon)
  })

  // 地図クリック以外でポップアップを閉じる
  map.getViewport().addEventListener('contextmenu', () => {
    if (popupElement) popupElement.style.display = 'none'
  })
}

function updateClickMarker(coordinate: Coordinate): void {
  if (!clickMarkerSource) return
  clickMarkerSource.clear()
  const feature = new Feature({ geometry: new Point(coordinate) })
  feature.setStyle(createClickMarkerStyle())
  clickMarkerSource.addFeature(feature)
}

function updateStationMarkers(stations: Station[]): void {
  if (!stationSource) return
  stationSource.clear()
  if (popupElement) popupElement.style.display = 'none'

  stations.forEach((station, index) => {
    const coord = fromLonLat([station.lon, station.lat])
    const feature = new Feature({ geometry: new Point(coord) })
    feature.setStyle(createStationStyle(index + 1))
    feature.set('type', 'station')
    feature.set('name', station.name)
    feature.set('distance', station.distanceMeters)
    stationSource!.addFeature(feature)
  })
}

function flyToStation(station: Station): void {
  if (!map) return
  map.getView().animate({
    center: fromLonLat([station.lon, station.lat]),
    zoom: 16,
    duration: 500,
  })
}

function panTo(lat: number, lon: number): void {
  if (!map) return
  const coord = fromLonLat([lon, lat])
  updateClickMarker(coord)
  map.getView().animate({
    center: coord,
    duration: 500,
  })
}

watch(
  () => props.stations,
  (newStations) => {
    updateStationMarkers(newStations)
  },
)

defineExpose({ flyToStation, panTo })

onMounted(() => {
  initMap()
})

onUnmounted(() => {
  map?.setTarget(undefined)
  map = null
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  min-height: 300px;
}
</style>

<style>
/* モバイルでアトリビューションテキストを非表示 */
@media (max-width: 768px) {
  .ol-attribution ul {
    display: none;
  }
}
</style>
