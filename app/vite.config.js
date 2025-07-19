import { sentryVitePlugin } from '@sentry/vite-plugin';
import { reactRouter } from '@react-router/dev/vite';
import { defineConfig } from 'vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
// import bundlesize from 'vite-plugin-bundlesize';

const gitpodWorkspace = process.env.GITPOD_WORKSPACE_URL;

export default defineConfig({
  plugins: [
    reactRouter(),
    !gitpodWorkspace && basicSsl(),
    // bundlesize({ limits: [{ name: 'assets/index-*.js', limit: '832.5 kB' }] }),
    sentryVitePlugin({
      org: 'elliana-may',
      project: 'media',
    }),
  ],
  envPrefix: 'REACT_APP_',
  build: {
    // to output your build into build dir the same as Webpack
    outDir: 'build',
    sourcemap: 'hidden',
  },
  ssr: {
    // Workaround for resolving dependencies in the server bundle
    // Without this, the React context will be different between direct import and transitive imports in development environment
    // For more information, see https://github.com/mui/material-ui/issues/45878#issuecomment-2987441663
    optimizeDeps: {
      include: ['@emotion/*', '@mui/*'],
    },
    noExternal: ['@emotion/*', '@mui/*'],
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
  root: __dirname,
});
