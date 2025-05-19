/// <reference types="vite/client" />

interface ViteTypeOptions {
  // By adding this line, you can make the type of ImportMetaEnv strict
  // to disallow unknown keys.
  strictImportMetaEnv: unknown;
}

interface ImportMetaEnv {
  readonly NODE_ENV: string | undefined;
  readonly REACT_APP_HEROKU_SLUG_COMMIT: string | undefined;
  readonly REACT_APP_API_PREFIX: string | undefined;
  readonly REACT_APP_AUTH0_CLIENT_ID: string | undefined;
  readonly REACT_APP_AUTH0_AUDIENCE: string | undefined;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
