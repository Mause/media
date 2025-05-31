const { fixupPluginRules } = require('@eslint/compat');
const eslint = require('@eslint/js');
const tseslint = require('typescript-eslint');
const eslintImport = require('eslint-plugin-import-x');
const {
  createTypeScriptImportResolver,
} = require('eslint-import-resolver-typescript');
const pluginDeprecation = require('eslint-plugin-deprecation');

module.exports = tseslint.config(
  eslint.configs.recommended,
  tseslint.configs.recommendedTypeChecked,
  tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: __dirname,
      },
    },
    plugins: {
      deprecation: fixupPluginRules(pluginDeprecation),
    },
    rules: {
      '@typescript-eslint/restrict-template-expressions': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
      '@typescript-eslint/no-unnecessary-type-parameters': 'off',

      'deprecation/deprecation': 'error',
      'import-x/no-named-as-default-member': 'off',
      'import-x/order': [
        'error',

        {
          'newlines-between': 'always',
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
