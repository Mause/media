import * as Sentry from '@sentry/browser';
import React from 'react';
import { Helmet } from 'react-helmet';
import { RouteProps } from 'react-router';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import { IndexComponent } from './IndexComponent';
import {
  EpisodeSelectComponent,
  SeasonSelectComponent,
} from './SeasonSelectComponent';
import { StatsComponent } from './StatsComponent';
import { SearchComponent } from './SearchComponent';
import ErrorBoundary, { FallbackProps } from 'react-error-boundary';
import { OptionsComponent } from './OptionsComponent';
import { load, MLink, ExtMLink } from './utils';
import { Link, Grid } from '@material-ui/core';
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

if (process.env.NODE_ENV === 'production') {
  Sentry.init({
    dsn: 'https://8b67269f943a4e3793144fdc31258b46@sentry.io/1869914',
    release: process.env.HEROKU_SLUG_COMMIT,
    environment: 'development',
  });
  Sentry.configureScope(scope => {
    scope.setUser((window as any).USER);
  });
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

function ParentComponentInt() {
  const classes = useStyles();
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
          <Grid item xs="auto">
            <Link href="/user/sign-out">Logout</Link>
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
                  {props.componentStack?.toString().split('\n').map(
                    line => <span key={line}>{line}<br /></span>
                  )}
                </pre>
              </code>
            </div>
          );
        }}
      >
        <Routes />
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
