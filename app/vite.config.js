import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import inject from '@rollup/plugin-inject';

import { nodePolyfills } from 'vite-plugin-node-polyfills';

export default defineConfig({
  plugins: [
    react(),
    nodePolyfills({
      overrides: {
        fs: 'browserfs/dist/shims/fs',
      },
    }),
    inject({
      BrowserFS: '/src/bfs.js',
    }),
  ],
  envPrefix: 'REACT_APP_',
  build: {
    // to output your build into build dir the same as Webpack
    outDir: 'build',
    sourcemap: true,
  },
  server: {
    open: true,
    port: 3000,
  },
});
