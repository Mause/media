import { StrictMode } from 'react';
import './index.css';
import { createRoot } from 'react-dom/client';
import { Auth0Provider } from '@auth0/auth0-react';
import {
  ThemeProvider,
  StyledEngineProvider,
  createTheme,
} from '@mui/material/styles';
import { HelmetProvider } from 'react-helmet-async';
import { useSentryToolbar } from '@sentry/toolbar';

import App from './App';

useSentryToolbar({
  // Remember to conditionally enable the Toolbar.
  // This will reduce network traffic for users
  // who do not have credentials to login to Sentry.
  enabled: true,
  initProps: {
    organizationSlug: 'acme',
    projectIdOrSlug: 'website',
  },
});

const theme = createTheme();

const clientId = import.meta.env.REACT_APP_AUTH0_CLIENT_ID;
const audience = import.meta.env.REACT_APP_AUTH0_AUDIENCE;

if (!(clientId && audience)) {
  console.error(
    'Missing Auth0 client ID or audience. Please check your environment variables.',
  );
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
        <HelmetProvider>
          <App />
        </HelmetProvider>
      </ThemeProvider>
    </StyledEngineProvider>
  </Auth0Provider>
);
root.render(<StrictMode>{rootEl}</StrictMode>);
