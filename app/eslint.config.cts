import { fixupPluginRules } from '@eslint/compat';
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import pluginDeprecation from 'eslint-plugin-deprecation';
import reactRefresh from 'eslint-plugin-react-refresh';
import { defineConfig } from 'eslint/config';

module.exports = defineConfig(
  eslint.configs.recommended,
  tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: __dirname,
      },
    },
    plugins: {
      // @ts-expect-error
      deprecation: fixupPluginRules(pluginDeprecation),
      'react-refresh': reactRefresh,
    },
    rules: {
      'deprecation/deprecation': 'error',
      'import-x/no-named-as-default-member': 'off',
      'no-restricted-imports': ['error', 'lodash'],
      '@typescript-eslint/consistent-type-imports': 'error',
      'react-refresh/only-export-components': [
        'error',
        {
          allowExportNames: [
            'meta',
            'links',
            'headers',
            'loader',
            'action',

            // TODO: remove getRoutes
            'getRoutes',
          ],
        },
      ],
    },
  },
);
