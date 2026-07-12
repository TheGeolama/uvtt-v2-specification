import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ command, mode }) => {
  // Injects subfolder routing during GitHub Action runs to prevent MIME type check errors on assets
  const base = process.env.VITE_BASE_PATH || './';

  return {
    plugins: [svelte()],
    base: base,
    server: {
      port: 3000,
      strictPort: true
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      target: 'esnext', // Target advanced WebGPU/PixiJS v8 compilations
      sourcemap: true,
      minify: 'esbuild'
    }
  };
});
