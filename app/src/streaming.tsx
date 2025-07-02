import { useSentryToolbar } from '@sentry/toolbar';
import * as Sentry from '@sentry/react';
import type { ErrorInfo, ReactNode } from 'react';
import type { RouteObject } from 'react-router-dom';
import {
  RouterProvider,
  createBrowserRouter,
  Outlet,
  useLocation,
  useMatches,
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
import { Loading } from './render';
import { RouteTitle } from './RouteTitle';

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
        {auth.isAuthenticated ||
        location.pathname === '/storybook' ||
        location.pathname == '/sitemap' ||
        match?.id === 'notFound' ? (
          <Outlet />
        ) : (
          <div>Please login</div>
        )}
      </ErrorBoundary>
    </>
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
  const router = createBrowserRouter(getRoutes());

  return <RouterProvider router={router} />;
}

function getRoutes() {
  return [
    {
      path: '/',
      element: (
        <SwrConfigWrapper>
          <ParentComponentInt />
        </SwrConfigWrapper>
      ),
      children: [
        {
          id: 'notFound',
          path: '*',
          element: (
            <RouteTitle title="Page not Found">
              <div>Page not found</div>
            </RouteTitle>
          ),
        },
        {
          path: '/websocket/:tmdbId',
          lazy: async () => {
            const { Websocket } = await import('./Websocket');
            return {
              element: (
                <RouteTitle title="Websocket">
                  <Websocket />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/select/:tmdb_id/options',
          lazy: async () => {
            const { OptionsComponent } = await import('./OptionsComponent');
            return {
              element: (
                <RouteTitle title="Movie Options">
                  <OptionsComponent type="movie" />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/select/:tmdb_id/season/:season/episode/:episode/options',
          lazy: async () => {
            const { OptionsComponent } = await import('./OptionsComponent');
            return {
              element: (
                <RouteTitle title="TV Options">
                  <OptionsComponent type="series" />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/select/:tmdb_id/season/:season/download_all',
          lazy: async () => {
            const { DownloadAllComponent } = await import(
              './DownloadAllComponent'
            );
            return {
              element: (
                <RouteTitle title="Download Season">
                  <DownloadAllComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/select/:tmdb_id/season/:season',
          lazy: async () => {
            const { EpisodeSelectComponent } = await import(
              './SeasonSelectComponent'
            );
            return {
              element: (
                <RouteTitle title="Select Episode">
                  <EpisodeSelectComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/select/:tmdb_id/season',
          lazy: async () => {
            const { SeasonSelectComponent } = await import(
              './SeasonSelectComponent'
            );
            return {
              element: (
                <RouteTitle title="Select Season">
                  <SeasonSelectComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/search',
          lazy: async () => {
            const { SearchComponent } = await import('./SearchComponent');
            return {
              element: (
                <RouteTitle title="Search">
                  <SearchComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/download',
          lazy: async () => {
            const { DownloadComponent } = await import('./DownloadComponent');
            return {
              element: (
                <RouteTitle title="Download">
                  <DownloadComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/manual',
          lazy: async () => {
            const { ManualAddComponent } = await import('./ManualAddComponent');
            return {
              element: (
                <RouteTitle title="Manual">
                  <ManualAddComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/stats',
          lazy: async () => {
            const { StatsComponent } = await import('./StatsComponent');
            return {
              element: (
                <RouteTitle title="Stats">
                  <StatsComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/diagnostics',
          lazy: async () => {
            const { DiagnosticsComponent } = await import(
              './DiagnosticsComponent'
            );
            return {
              element: (
                <RouteTitle title="Diagnostics">
                  <DiagnosticsComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/storybook',
          lazy: async () => {
            const { Storybook } = await import('./Storybook');
            return {
              element: (
                <RouteTitle title="Storybook">
                  <Storybook />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/monitor/delete/:id',
          lazy: async () => {
            const { MonitorDeleteComponent } = await import(
              './MonitorComponent'
            );
            return {
              element: (
                <RouteTitle title="Monitor">
                  <MonitorDeleteComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/monitor',
          lazy: async () => {
            const { MonitorComponent } = await import('./MonitorComponent');
            return {
              element: (
                <RouteTitle title="Monitor">
                  <MonitorComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/sitemap',
          element: (
            <RouteTitle title="Sitemap">
              <SitemapRoot />
            </RouteTitle>
          ),
        },
        {
          path: '/discover',
          hydrateFallbackElement: <Loading loading />,
          lazy: async () => {
            const { DiscoveryComponent } = await import('./DiscoveryComponent');
            return {
              element: (
                <RouteTitle title="Discover">
                  <DiscoveryComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/',
          lazy: async () => {
            const { IndexComponent } = await import('./IndexComponent');
            return {
              element: (
                <RouteTitle title="Media">
                  <IndexComponent />
                </RouteTitle>
              ),
            };
          },
        },
      ],
    },
  ] satisfies RouteObject[];
}

function SitemapRoot() {
  return <Sitemap routes={getRoutes()} />;
}
function Sitemap({ routes }: { routes: RouteObject[] }) {
  return (
    <ul>
      {routes.map((route) => (
        <li key={route.path}>
          <MLink to={route.path!}>{route.path}</MLink>
          {route.children ? <Sitemap routes={route.children} /> : undefined}
        </li>
      ))}
    </ul>
  );
}
