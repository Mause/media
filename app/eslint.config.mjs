import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactPlugin from 'eslint-plugin-react';
import importPlugin from 'eslint-plugin-import';

export default tseslint.config(
  eslint.configs.recommended,
  tseslint.configs.recommendedTypeChecked,
  tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    settings: {
      react: {
        version: '18',
      },
      'import/resolver': {
        typescript: true,
        node: true,
      },
    },
  },
  reactPlugin.configs.flat.recommended, // This is not a plugin object, but a shareable config object
  reactPlugin.configs.flat['jsx-runtime'], // Add this if you are using React 17+
  importPlugin.flatConfigs.recommended,
  importPlugin.flatConfigs.typescript,
);
