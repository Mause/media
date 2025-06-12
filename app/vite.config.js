import react from '@vitejs/plugin-react-oxc';
import { defineConfig } from 'vite';
import basicSsl from '@vitejs/plugin-basic-ssl';

export default defineConfig({
  plugins: [react(), basicSsl()],
  envPrefix: 'REACT_APP_',
  build: {
    // to output your build into build dir the same as Webpack
    outDir: 'build',
    sourcemap: true,
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
