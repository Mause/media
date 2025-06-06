import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  envPrefix: 'REACT_APP_',
  build: {
    // to output your build into build dir the same as Webpack
    outDir: 'build',
    sourcemap: true,
    rollupOptions: { external: ['util', 'fs'] },
  },
  server: {
    open: true,
    port: 3000,
  },
});
