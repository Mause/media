import { fixupPluginRules } from '@eslint/compat';
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import eslintImport from 'eslint-plugin-import-x';
import { createTypeScriptImportResolver } from 'eslint-import-resolver-typescript';
import pluginDeprecation from 'eslint-plugin-deprecation';
import reactRefresh from 'eslint-plugin-react-refresh';

const DefaultOptions = eslintImport.rules.order.defaultOptions[0];

module.exports = tseslint.config(
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
      'import-x/order': [
        'error',
        {
          'newlines-between': 'always',
        } satisfies typeof DefaultOptions,
      ],
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
    settings: {
      'import-x/resolver-next': [createTypeScriptImportResolver({})],
    },
  },
  eslintImport.flatConfigs.recommended,
  eslintImport.flatConfigs.typescript,
  eslintImport.flatConfigs.react,
);
