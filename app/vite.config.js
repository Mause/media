import { reactRouter } from '@react-router/dev/vite';
import { defineConfig } from 'vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import bundlesize from 'vite-plugin-bundlesize';

export default defineConfig({
  plugins: [
    reactRouter(),
    basicSsl(),
    bundlesize({ limits: [{ name: 'assets/index-*.js', limit: '832.5 kB' }] }),
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
  root: __dirname,
});
