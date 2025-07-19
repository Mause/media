import type { ReactNode } from 'react';
import { Scripts, Outlet, useLoaderData } from 'react-router-dom';
import { StrictMode } from 'react';
import './index.css';
import { Auth0Provider } from '@auth0/auth0-react';
import {
  ThemeProvider,
  StyledEngineProvider,
  createTheme,
} from '@mui/material/styles';

import { Loading } from './components/Loading';

const theme = createTheme();

const clientId = import.meta.env.REACT_APP_AUTH0_CLIENT_ID;
const audience = import.meta.env.REACT_APP_AUTH0_AUDIENCE;

if (!(clientId && audience)) {
  console.error(
    'Missing Auth0 client ID or audience. Please check your environment variables.',
  );
}

export function HydrateFallback() {
  return <Loading loading />;
}

export function clientLoader() {
  return { origin: window.location.origin };
}

export function loader({ request }: { request: Request }) {
  return { origin: new URL(request.url).origin };
}

export function Layout({ children }: { children: ReactNode }) {
  const { origin } = useLoaderData<typeof loader>();
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <link rel="icon" href="/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#000000" />
        <meta
          name="description"
          content="Web site created using create-react-app"
        />
        <link rel="apple-touch-icon" href="/logo192.png" />
        <title>Media</title>
      </head>
      <body>
        <StrictMode>
          <Auth0Provider
            domain="mause.au.auth0.com"
            clientId={clientId!}
            authorizationParams={{
              audience: audience!,
              redirect_uri: origin,
            }}
            useRefreshTokensFallback={true}
            useRefreshTokens={true}
            cacheLocation="localstorage"
          >
            <StyledEngineProvider injectFirst>
              <ThemeProvider theme={theme}>{children}</ThemeProvider>
            </StyledEngineProvider>
          </Auth0Provider>
        </StrictMode>
        <Scripts />
      </body>
    </html>
  );
}

export default function Root() {
  return <Outlet />;
}
