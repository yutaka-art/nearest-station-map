/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// GitHub Pages にデプロイする場合は base を設定してください。
// 例: base: '/nearest-station-map/'
// Vercel や通常の Web サーバーの場合は base: '/' のまま（または省略）でOKです。
export default defineConfig({
  plugins: [vue()],
  base: '/',
  test: {
    environment: 'node',
  },
})
