/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // GitHub Pages のリポジトリ名サブパスに合わせる
  base: '/nearest-station-map/',
  test: {
    environment: 'node',
  },
})
