import { StrictMode, useEffect } from 'react';
import './index.css';
import { createRoot } from 'react-dom/client';
import { Auth0Provider } from '@auth0/auth0-react';
import {
  ThemeProvider,
  StyledEngineProvider,
  createTheme,
} from '@mui/material/styles';
import * as Sentry from '@sentry/react';
import {
  useLocation,
  useNavigationType,
  createRoutesFromChildren,
  matchRoutes,
} from 'react-router-dom';

import { ParentComponent } from './ParentComponent';

const theme = createTheme();

const clientId = import.meta.env.REACT_APP_AUTH0_CLIENT_ID;
const audience = import.meta.env.REACT_APP_AUTH0_AUDIENCE;

if (!(clientId && audience)) {
  console.error(
    'Missing Auth0 client ID or audience. Please check your environment variables.',
  );
}
if (import.meta.env.NODE_ENV === 'production') {
  Sentry.init({
    dsn: 'https://8b67269f943a4e3793144fdc31258b46@sentry.io/1869914',
    release: import.meta.env.REACT_APP_HEROKU_SLUG_COMMIT,
    environment: 'development',
    integrations: [
      Sentry.reactRouterV7BrowserTracingIntegration({
        trackFetchStreamPerformance: true,
        useEffect,
        useLocation,
        useNavigationType,
        createRoutesFromChildren,
        matchRoutes,
      }),
    ],
    // Adds request headers and IP for users, for more info visit:
    // https://docs.sentry.io/platforms/javascript/guides/react/configuration/options/#sendDefaultPii
    sendDefaultPii: true,

    // Enable logs to be sent to Sentry
    enableLogs: true,
    tracesSampleRate: 1.0,
  });
}

const container = document.getElementById('root');
const root = createRoot(container!);
const rootEl = (
  <Auth0Provider
    domain="mause.au.auth0.com"
    clientId={clientId!}
    authorizationParams={{
      audience: audience!,
      redirect_uri: window.location.origin,
    }}
    useRefreshTokensFallback={true}
    useRefreshTokens={true}
    cacheLocation="localstorage"
  >
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={theme}>
        <ParentComponent />
      </ThemeProvider>
    </StyledEngineProvider>
  </Auth0Provider>
);
root.render(<StrictMode>{rootEl}</StrictMode>);
