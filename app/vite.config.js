import react from '@vitejs/plugin-react-oxc';
import { defineConfig } from 'vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import bundlesize from 'vite-plugin-bundlesize';

export default defineConfig({
  plugins: [
    react(),
    basicSsl(),
    bundlesize({ limits: [{ name: 'assets/index-*.js', limit: '868.9 kB' }] }),
  ],
  envPrefix: 'REACT_APP_',
  build: {
    // to output your build into build dir the same as Webpack
    outDir: 'build',
    sourcemap: 'hidden',
  },
  server: {
    open: true,
    port: 3000,
    https: true,
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
});
