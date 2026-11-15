import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

// In development Vite forwards /api and /resources to the API, as nginx does
// when deployed (ADR-007): the application only ever calls relative paths.
const api = process.env.IEKG_DEV_API ?? 'http://127.0.0.1:8000';
const proxy = { '/api': api, '/resources': api };

export default defineConfig({
  plugins: [svelte()],
  server: { port: 5173, strictPort: true, proxy },
  preview: { port: 4173, strictPort: true, proxy },
});
