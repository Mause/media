import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { pigment } from '@pigment-css/vite-plugin';

import { createTheme } from '@mui/material';

/**
 * @type {import('@pigment-css/vite-plugin').PigmentOptions}
 */
 const pigmentConfig = {
   transformLibraries: ['@mui/material'],
  theme: createTheme({
    cssVariables: true,
    /* other parameters, if any */
  }),
};

export default defineConfig({
  plugins: [
    pigment(pigmentConfig),
  react()],
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
