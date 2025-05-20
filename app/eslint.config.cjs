const eslint = require('@eslint/js');
const tseslint = require('typescript-eslint');
const eslintImport = require('eslint-plugin-import-x');
const {
  createTypeScriptImportResolver,
} = require('eslint-import-resolver-typescript');

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
    rules: {
      'import-x/no-named-as-default-member': 'off',
      'import-x/order': 'error',
    },
    settings: {
      'import-x/resolver-next': [createTypeScriptImportResolver({})],
    },
  },
  eslintImport.flatConfigs.recommended,
  eslintImport.flatConfigs.typescript,
  eslintImport.flatConfigs.react,
);
