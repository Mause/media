import * as Sentry from '@sentry/browser';
import React from 'react';
import Helmet from 'react-helmet';
import ReactLoading from 'react-loading';
import { RouteProps, Redirect } from 'react-router';
import {
  BrowserRouter as Router,
  Route,
  useLocation,
  Switch,
} from 'react-router-dom';
import { IndexComponent } from './IndexComponent';
import {
  EpisodeSelectComponent,
  SeasonSelectComponent,
} from './SeasonSelectComponent';
import { StatsComponent } from './StatsComponent';
import { SearchComponent } from './SearchComponent';
import ErrorBoundary, { FallbackProps } from 'react-error-boundary';
import { OptionsComponent } from './OptionsComponent';
import { load, usePost, MLink } from './utils';
import AxiosErrorCatcher from './AxiosErrorCatcher';
import { Link as MaterialLink } from '@material-ui/core';
import { SWRConfig } from 'swr';
import { MonitorComponent, MonitorAddComponent } from './MonitorComponent';
import { ManualAddComponent } from './ManualAddComponent';
import { makeStyles, Theme, createStyles } from '@material-ui/core';

Sentry.init({
  dsn: 'https://8b67269f943a4e3793144fdc31258b46@sentry.io/1869914',
  release: process.env.HEROKU_SLUG_COMMIT,
  environment:
    process.env.NODE_ENV === 'production' ? 'production' : 'development',
});
Sentry.configureScope(scope => {
  scope.setUser((window as any).USER);
});

export function DownloadComponent() {
  const { state } = useLocation<{
    tmdb_id: string;
    magnet: string;
    season?: string;
    episode?: string;
  }>();

  const [done] = usePost('download', [
    {
      tmdb_id: state!.tmdb_id,
      magnet: state.magnet,
      season: state.season,
      episode: state.episode,
    },
  ]);

  return done ? <Redirect to="/" /> : <ReactLoading color="#000000" />;
}

export interface IndexResponse {
  series: SeriesResponse[];
  movies: MovieResponse[];
}
export interface Download {
  id: number;
  imdb_id: string;
  title: string;
  transmission_id: string;
  added_by?: { first_name: string };
}
export interface MovieResponse {
  download: Download;
  id: number;
}
export interface SeriesResponse {
  imdb_id: string;
  tmdb_id: string;
  title: string;
  seasons: {
    [key: string]: EpisodeResponse[];
  };
}
export interface EpisodeResponse {
  download: Download;
  episode: number;
  id: number;
  season: number;
  show_title: string;
}
export interface TorrentFile {
  name: string;
  bytesCompleted: number;
  length: number;
}
export type Torrents = {
  [key: string]: { eta: number; percentDone: number; files: TorrentFile[] };
};

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
  Sentry.withScope(scope => {
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

function ExtMLink(props: { href: string; children: string }) {
  return (
    <MaterialLink href={props.href} target="_blank" rel="noopener noreferrer">
      {props.children}
    </MaterialLink>
  );
}

function ParentComponentInt() {
  const classes = useStyles();
  return (
    <Router>
      <h1>Media</h1>

      <nav className={classes.root}>
        <MLink to="/">Home</MLink>
        <MLink to="/monitor">Monitors</MLink>
        <ExtMLink href="http://novell.mause.me:9091">Transmission</ExtMLink>
        <ExtMLink href="https://app.plex.tv">Plex</ExtMLink>
        <a href="/user/sign-out">Logout</a>
      </nav>

      <br />

      <ErrorBoundary
        onError={reportError}
        FallbackComponent={(props: FallbackProps) => (
          <div>An error has occured: {props.error!!.message}</div>
        )}
      >
        <AxiosErrorCatcher>
          <Routes />
        </AxiosErrorCatcher>
      </ErrorBoundary>
    </Router>
  );
}
export function swrConfig(WrappedComponent: React.ComponentType<{}>) {
  return () => (
    <SWRConfig
      value={{
        // five minute refresh
        refreshInterval: 5 * 60 * 1000,
        fetcher: (...args) => load(args[0], args[1]),
      }}
    >
      <WrappedComponent />
    </SWRConfig>
  );
}
const ParentComponent = swrConfig(ParentComponentInt);

function Routes() {
  return (
    <Switch>
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
