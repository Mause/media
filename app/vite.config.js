import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import bundlesize from 'vite-plugin-bundlesize';
import { VitePWA } from 'vite-plugin-pwa';

const gitpodWorkspace = process.env.GITPOD_WORKSPACE_URL;

export default defineConfig({
  plugins: [
    react(),
    gitpodWorkspace && basicSsl(),
    bundlesize({ limits: [{ name: 'assets/index-*.js', limit: '832.5 kB' }] }),
    VitePWA(),
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
    https: !gitpodWorkspace,
    allowedHosts: gitpodWorkspace && ['3000-' + new URL(gitpodWorkspace).host],
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
});
