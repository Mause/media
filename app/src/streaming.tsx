import { useSentryToolbar } from '@sentry/toolbar';
import * as Sentry from '@sentry/react';
import type { ErrorInfo, ReactNode } from 'react';
import { useEffect } from 'react';
import {
  RouterProvider,
  createBrowserRouter,
  Outlet,
  useLocation,
  useMatches,
  createRoutesFromChildren,
  matchRoutes,
  useNavigationType,
} from 'react-router-dom';
import type { FallbackProps } from 'react-error-boundary';
import { ErrorBoundary } from 'react-error-boundary';
import { Grid, Link as MaterialLink } from '@mui/material';
import { styled } from '@mui/material/styles';
import { SWRConfig } from 'swr';
import { useProfiler } from '@sentry/react';
import { useAuth0 } from '@auth0/auth0-react';
import * as _ from 'lodash-es';

import { load, getToken } from './utils';
import type { components } from './schema';
import { ExtMLink, MLink } from './MLink';
import routes from './routes';

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
    _experiments: { enableLogs: true },
    tracesSampleRate: 1.0,
  });
}

export type TorrentFile = components['schemas']['InnerTorrentFile'];
export type Torrents = { [key: string]: components['schemas']['InnerTorrent'] };
export type IndexResponse = components['schemas']['IndexResponse'];
export type MovieResponse = components['schemas']['MovieDetailsSchema'];
export type SeriesResponse = components['schemas']['SeriesDetails'];
export type EpisodeResponse = components['schemas']['EpisodeDetailsSchema'];

function reportError(error: Error, info: ErrorInfo) {
  Sentry.withScope((scope) => {
    scope.setExtras({
      componentStack: info.componentStack,
      digest: info.digest,
    });
    const eventId = Sentry.captureException(error);
    Sentry.showReportDialog({ eventId });
  });
}

const PREFIX = 'ParentComponentInt';
const classes = {
  root: `${PREFIX}-root`,
};
const NavRoot = styled('nav')(({ theme }) => ({
  [`& .${classes.root}`]: {
    margin: theme.spacing(1),
    linkStyle: 'underline',
  },
}));

const Login = () => {
  const { loginWithRedirect, isAuthenticated, logout } = useAuth0();

  if (isAuthenticated) {
    return (
      <MaterialLink href="#" onClick={() => void logout({})} underline="hover">
        Logout
      </MaterialLink>
    );
  } else {
    return (
      <MaterialLink
        href="#"
        onClick={() => void loginWithRedirect({})}
        underline="hover"
      >
        Login
      </MaterialLink>
    );
  }
};

export function ParentComponentInt() {
  useProfiler('ParentComponentInt');

  const auth = useAuth0();
  const location = useLocation();
  const match = _.last(useMatches());
  console.log({ user: auth.user });

  useSentryToolbar({
    // Remember to conditionally enable the Toolbar.
    // This will reduce network traffic for users
    // who do not have credentials to login to Sentry.
    enabled: auth.user?.nickname === 'me',
    initProps: {
      organizationSlug: 'elliana-may',
      projectIdOrSlug: 'media',
    },
  });

  return (
    <SwrConfigWrapper>
      <h1>Media</h1>

      <NavRoot className={classes.root}>
        <Grid container spacing={1}>
          <Grid size={{ xs: 'auto' }}>
            <MLink to="/">Home</MLink>
          </Grid>
          <Grid size={{ xs: 'auto' }}>
            <MLink to="/monitor">Monitors</MLink>
          </Grid>
          <Grid size={{ xs: 'auto' }}>
            <ExtMLink href="http://novell.mause.me:9091">Transmission</ExtMLink>
          </Grid>
          <Grid size={{ xs: 'auto' }}>
            <ExtMLink href="https://app.plex.tv">Plex</ExtMLink>
          </Grid>
          <Grid size={{ xs: 'auto' }}>
            <MLink to="/discover">Discover</MLink>
          </Grid>
          {auth.user && <Grid size={{ xs: 'auto' }}>{auth.user.name}</Grid>}
          <Grid size={{ xs: 'auto' }}>
            <Login />
          </Grid>
        </Grid>
      </NavRoot>

      <br />

      <ErrorBoundary
        onError={reportError}
        FallbackComponent={(props: FallbackProps) => {
          const error = props.error as Error;
          return (
            <div>
              An error has occured:
              <code>
                <pre>
                  {error.message}
                  {error.stack
                    ?.toString()
                    .split('\n')
                    .map((line: string) => (
                      <span key={line}>
                        {line}
                        <br />
                      </span>
                    ))}
                </pre>
              </code>
              <button onClick={props.resetErrorBoundary}>Retry</button>
            </div>
          );
        }}
      >
        {auth.isAuthenticated ||
        location.pathname === '/storybook' ||
        location.pathname == '/sitemap' ||
        match?.id === 'notFound' ? (
          <Outlet />
        ) : (
          <div>Please login</div>
        )}
      </ErrorBoundary>
    </SwrConfigWrapper>
  );
}
export function SwrConfigWrapper({ children }: { children: ReactNode }) {
  const auth = useAuth0();
  return (
    <SWRConfig
      value={{
        // five minute refresh
        refreshInterval: 5 * 60 * 1000,
        fetcher: async (path: string, params: string) =>
          await load(
            path,
            params,
            auth.isAuthenticated
              ? {
                  Authorization: 'Bearer ' + (await getToken(auth)),
                }
              : {},
          ),
      }}
    >
      {children}
    </SWRConfig>
  );
}

export function ParentComponent() {
  // Call this AFTER Sentry.init()
  const sentryCreateBrowserRouter =
    Sentry.wrapCreateBrowserRouterV7(createBrowserRouter);

  const router = sentryCreateBrowserRouter(routes);

  return <RouterProvider router={router} />;
}
