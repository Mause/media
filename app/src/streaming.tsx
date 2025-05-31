import * as Sentry from '@sentry/react';
import { ErrorInfo } from 'react';
import { Helmet } from 'react-helmet-async';
import {
  RouterProvider,
  createBrowserRouter,
  Outlet,
  RouteObject,
  useLocation,
} from 'react-router-dom';
import { ErrorBoundary, FallbackProps } from 'react-error-boundary';
import { Grid, Link as MaterialLink } from '@mui/material';
import { styled } from '@mui/material/styles';
import { SWRConfig } from 'swr';
import { useProfiler } from '@sentry/react';
import { useAuth0 } from '@auth0/auth0-react';

import { IndexComponent } from './IndexComponent';
import {
  EpisodeSelectComponent,
  SeasonSelectComponent,
} from './SeasonSelectComponent';
import { StatsComponent } from './StatsComponent';
import { SearchComponent } from './SearchComponent';
import { OptionsComponent } from './OptionsComponent';
import { load, MLink, ExtMLink } from './utils';
import { MonitorComponent, MonitorDeleteComponent } from './MonitorComponent';
import { ManualAddComponent } from './ManualAddComponent';
import { DownloadComponent } from './DownloadComponent';
import { DownloadAllComponent } from './DownloadAllComponent';
import { Websocket } from './Websocket';
import { components } from './schema';
import { DiagnosticsComponent } from './DiagnosticsComponent';
import Storybook from './Storybook';

if (import.meta.env.NODE_ENV === 'production') {
  Sentry.init({
    dsn: 'https://8b67269f943a4e3793144fdc31258b46@sentry.io/1869914',
    release: import.meta.env.REACT_APP_HEROKU_SLUG_COMMIT,
    environment: 'development',
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate: 0.75, // must be present and non-zero
  });
}

export type TorrentFile = components['schemas']['InnerTorrentFile'];
export type Torrents = { [key: string]: components['schemas']['InnerTorrent'] };
export type IndexResponse = components['schemas']['IndexResponse'];
export type MovieResponse = components['schemas']['MovieDetailsSchema'];
export type SeriesResponse = components['schemas']['SeriesDetails'];
export type EpisodeResponse = components['schemas']['EpisodeDetailsSchema'];

function RouteTitle({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <>
      <Helmet>
        <title>{title}</title>
      </Helmet>
      {children}
    </>
  );
}

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

function ParentComponentInt() {
  useProfiler('ParentComponentInt');

  const auth = useAuth0();
  const location = useLocation();
  console.log({ user: auth.user });

  return (
    <>
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
        {auth.isAuthenticated || location.pathname === '/storybook' ? (
          <Outlet />
        ) : (
          <div>Please login</div>
        )}
      </ErrorBoundary>
    </>
  );
}
export function SwrConfigWrapper({ children }: { children: React.ReactNode }) {
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
                  Authorization:
                    'Bearer ' + (await auth.getAccessTokenSilently()),
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
  const router = createBrowserRouter(getRoutes());

  return <RouterProvider router={router} />;
}

function getRoutes() {
  const routes = [
    {
      path: '/',
      element: (
        <SwrConfigWrapper>
          <ParentComponentInt />
        </SwrConfigWrapper>
      ),
      children: [
        {
          path: '*',
          element: (
            <RouteTitle title="Page not Found">
              <div>Page not found</div>
            </RouteTitle>
          ),
        },
        {
          path: '/websocket/:tmdbId',
          element: (
            <RouteTitle title="Websocket">
              <Websocket />
            </RouteTitle>
          ),
        },
        {
          path: '/select/:tmdb_id/options',
          element: (
            <RouteTitle title="Movie Options">
              <OptionsComponent type="movie" />
            </RouteTitle>
          ),
        },

        {
          path: '/select/:tmdb_id/season/:season/episode/:episode/options',
          element: (
            <RouteTitle title="TV Options">
              <OptionsComponent type="series" />
            </RouteTitle>
          ),
        },
        {
          path: '/select/:tmdb_id/season/:season/download_all',
          element: (
            <RouteTitle title="Download Season">
              <DownloadAllComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/select/:tmdb_id/season/:season',
          element: (
            <RouteTitle title="Select Episode">
              <EpisodeSelectComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/select/:tmdb_id/season',
          element: (
            <RouteTitle title="Select Season">
              <SeasonSelectComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/search',
          element: (
            <RouteTitle title="Search">
              <SearchComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/download',
          element: (
            <RouteTitle title="Download">
              <DownloadComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/manual',
          element: (
            <RouteTitle title="Manual">
              <ManualAddComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/stats',
          element: (
            <RouteTitle title="Stats">
              <StatsComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/diagnostics',
          element: (
            <RouteTitle title="Diagnostics">
              <DiagnosticsComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/storybook',
          element: (
            <RouteTitle title="Storybook">
              <Storybook />
            </RouteTitle>
          ),
        },
        {
          path: '/monitor/delete/:id',
          element: (
            <RouteTitle title="Monitor">
              <MonitorDeleteComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/monitor',
          element: (
            <RouteTitle title="Monitor">
              <MonitorComponent />
            </RouteTitle>
          ),
        },
        {
          path: '/',
          element: (
            <RouteTitle title="Media">
              <IndexComponent />
            </RouteTitle>
          ),
        },
      ],
    },
  ] satisfies RouteObject[];
  return routes;
}
