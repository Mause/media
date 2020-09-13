import * as Sentry from '@sentry/react';
import React from 'react';
import { Helmet } from 'react-helmet';
import {
  RouteProps,
  BrowserRouter as Router,
  Route,
  Switch,
} from 'react-router-dom';
import { IndexComponent } from './IndexComponent';
import {
  EpisodeSelectComponent,
  SeasonSelectComponent,
} from './SeasonSelectComponent';
import { StatsComponent } from './StatsComponent';
import { SearchComponent } from './SearchComponent';
import { ErrorBoundary, FallbackProps } from 'react-error-boundary';
import { OptionsComponent } from './OptionsComponent';
import { load, MLink, ExtMLink } from './utils';
import { Grid } from '@material-ui/core';
import { SWRConfig } from 'swr';
import {
  MonitorComponent,
  MonitorAddComponent,
  MonitorDeleteComponent,
} from './MonitorComponent';
import { ManualAddComponent } from './ManualAddComponent';
import { makeStyles, Theme, createStyles } from '@material-ui/core';
import { DownloadComponent } from './DownloadComponent';
import { DownloadAllComponent } from './DownloadAllComponent';
import { Websocket } from './Websocket';
import { Integrations as ApmIntegrations } from '@sentry/apm';
import { useProfiler } from '@sentry/react';
import { useAuth0 } from '@auth0/auth0-react';
import { Link as MaterialLink } from '@material-ui/core';
import { components } from './schema';

if (process.env.NODE_ENV === 'production') {
  Sentry.init({
    dsn: 'https://8b67269f943a4e3793144fdc31258b46@sentry.io/1869914',
    release: process.env.HEROKU_SLUG_COMMIT,
    environment: 'development',
    integrations: [new ApmIntegrations.Tracing()],
    tracesSampleRate: 0.75, // must be present and non-zero
  });
  Sentry.configureScope((scope) => {
    scope.setUser((window as any).USER);
  });
}

export type Torrents = { [key: string]: components['schemas']['InnerTorrent'] };
export type IndexResponse = components['schemas']['IndexResponse'];
export type MovieResponse = components['schemas']['MovieDetailsSchema'];
export type SeriesResponse = components['schemas']['SeriesDetails'];
export type EpisodeResponse = components['schemas']['EpisodeDetailsSchema'];

function RouteWithTitle({ title, ...props }: { title: string } & RouteProps) {
  return (
    <>
      <Helmet>
        <title>{title}</title>
      </Helmet>
      <Route {...props} strict={true} />
    </>
  );
}

function reportError(error: Error, componentStack: string) {
  Sentry.withScope((scope) => {
    scope.setExtras({ stack: componentStack });
    const eventId = Sentry.captureException(error);
    Sentry.showReportDialog({ eventId: eventId });
  });
}

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      '& > *': {
        margin: theme.spacing(1),
        linkStyle: 'underline',
      },
    },
  }),
);

const Login = () => {
  const { loginWithRedirect, isAuthenticated, logout } = useAuth0();

  if (isAuthenticated) {
    return (
      <MaterialLink href="#" onClick={() => logout({})}>
        Logout
      </MaterialLink>
    );
  } else {
    return (
      <MaterialLink href="#" onClick={() => loginWithRedirect({})}>
        Login
      </MaterialLink>
    );
  }
};

function ParentComponentInt() {
  useProfiler('ParentComponentInt');
  const classes = useStyles();

  const auth = useAuth0();
  console.log(auth.user);

  return (
    <Router>
      <h1>Media</h1>

      <nav className={classes.root}>
        <Grid container spacing={1}>
          <Grid item xs="auto">
            <MLink to="/">Home</MLink>
          </Grid>
          <Grid item xs="auto">
            <MLink to="/monitor">Monitors</MLink>
          </Grid>
          <Grid item xs="auto">
            <ExtMLink href="http://novell.mause.me:9091">Transmission</ExtMLink>
          </Grid>
          <Grid item xs="auto">
            <ExtMLink href="https://app.plex.tv">Plex</ExtMLink>
          </Grid>
          {auth.user && (
            <Grid item xs="auto">
              {auth.user.name}
            </Grid>
          )}
          <Grid item xs="auto">
            <Login />
          </Grid>
        </Grid>
      </nav>

      <br />

      <ErrorBoundary
        onError={reportError}
        FallbackComponent={(props: FallbackProps) => {
          return (
            <div>
              An error has occured:
              <code>
                <pre>
                  {props.error!!.message}
                  {props
                    .error!!.stack?.toString()
                    .split('\n')
                    .map((line) => (
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
        <Routes />
      </ErrorBoundary>
    </Router>
  );
}
function SwrConfigWrapper({
  WrappedComponent,
}: {
  WrappedComponent: React.ComponentType<{}>;
}) {
  const auth = useAuth0();
  return (
    <SWRConfig
      value={{
        // five minute refresh
        refreshInterval: 5 * 60 * 1000,
        fetcher: async (path, params) =>
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
      <WrappedComponent />
    </SWRConfig>
  );
}

export function swrConfig(WrappedComponent: React.ComponentType<{}>) {
  return () => <SwrConfigWrapper WrappedComponent={WrappedComponent} />;
}
const ParentComponent = swrConfig(ParentComponentInt);

function Routes() {
  const auth = useAuth0();

  if (!auth.isAuthenticated) return <div>Please login</div>;

  return (
    <Switch>
      <RouteWithTitle path="/websocket/:tmdbId" title="Websocket">
        <Websocket />
      </RouteWithTitle>
      <RouteWithTitle path="/select/:tmdb_id/options" title="Movie Options">
        <OptionsComponent type="movie" />
      </RouteWithTitle>
      <RouteWithTitle
        path="/select/:tmdb_id/season/:season/episode/:episode/options"
        title="TV Options"
      >
        <OptionsComponent type="series" />
      </RouteWithTitle>
      <RouteWithTitle
        path="/select/:tmdb_id/season/:season/download_all"
        title="Download Season"
      >
        <DownloadAllComponent />
      </RouteWithTitle>
      <RouteWithTitle
        path="/select/:tmdb_id/season/:season"
        title="Select Episode"
      >
        <EpisodeSelectComponent />
      </RouteWithTitle>
      <RouteWithTitle path="/select/:tmdb_id/season" title="Select Season">
        <SeasonSelectComponent />
      </RouteWithTitle>
      <RouteWithTitle path="/search" title="Search">
        <SearchComponent />
      </RouteWithTitle>
      <RouteWithTitle path="/download" title="Download">
        <DownloadComponent />
      </RouteWithTitle>
      <RouteWithTitle path="/manual" title="Manual">
        <ManualAddComponent />
      </RouteWithTitle>
      <RouteWithTitle path="/stats" title="Stats">
        <StatsComponent />
      </RouteWithTitle>
      <RouteWithTitle path="/monitor/delete/:id" title="Monitor">
        <MonitorDeleteComponent />
      </RouteWithTitle>
      <RouteWithTitle path="/monitor/add/:tmdb_id" title="Monitor">
        <MonitorAddComponent />
      </RouteWithTitle>
      <RouteWithTitle path="/monitor" title="Monitor">
        <MonitorComponent />
      </RouteWithTitle>
      <RouteWithTitle path="/" title="Media">
        <IndexComponent />
      </RouteWithTitle>
    </Switch>
  );
}
export { ParentComponent };
