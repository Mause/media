import * as Sentry from '@sentry/browser';
import _ from 'lodash';
import qs from 'qs';
import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import Helmet from 'react-helmet';
import ReactLoading from 'react-loading';
import { RouteProps, Redirect } from 'react-router';
import { BrowserRouter as Router, Link, Route, RouteComponentProps, Switch, withRouter } from 'react-router-dom';
import './app.css';
import { IndexComponent } from './IndexComponent';
import { EpisodeSelectComponent, SeasonSelectComponent } from './SeasonSelectComponent';
import Axios from 'axios';
import { StatsComponent } from './StatsComponent';
import { SearchComponent } from './SearchComponent';
import { OptionsComponent } from './OptionsComponent';

Sentry.init({
  dsn: "https://8b67269f943a4e3793144fdc31258b46@sentry.io/1869914",
  release: process.env.HEROKU_SLUG_COMMIT,
  environment: process.env.NODE_ENV === 'production' ? 'production' : 'development',
});

class _DownloadComponent extends Component<RouteComponentProps<{}>, { done?: boolean }> {
  constructor(props: RouteComponentProps<{}>) {
    debugger;
    super(props);
    this.state = {};
  }
  componentDidMount() {
    const state = this.props.location.state;
    const url = `/download/${state.type}?` +
      qs.stringify({
        imdb_id: state.imdb_id,
        magnet: state.magnet,
        titles: state.titles,
      });
    Axios.get(url).then(() => {
      debugger;
      this.setState({ done: true })
    })
  }
  render() {
    return this.state.done ? <Redirect to='/' /> : <ReactLoading type='balls' color='#000000' />;
  }
}
const DownloadComponent = withRouter(_DownloadComponent);

export interface IndexResponse {
  series: SeriesResponse[];
  movies: MovieResponse[];
}
export interface Download {
  id: number;
  imdb_id: string;
  title: string,
  transmission_id: string,
  added_by?: { first_name: string }
}
export interface MovieResponse {
  download: Download,
  id: number
}
export interface SeriesResponse {
  imdb_id: string;
  tmdb_id: string;
  title: string;
  seasons: {
    [key: string]:
    EpisodeResponse[]
  };
}
export interface EpisodeResponse {
  download: Download,
  episode: number,
  id: number,
  season: number,
  show_title: string;
}
export interface TorrentFile {
  name: string;
  bytesCompleted: number;
  length: number;
}
export type Torrents = { [key: string]: { eta: number, percentDone: number, files: TorrentFile[] } }

function RouteWithTitle({ title, ...props }: { title: string } & RouteProps) {
  return (
    <>
      <Helmet>
        <title>{title}</title>
      </Helmet>
      <Route {...props} strict={true} />
    </>
  )
}

function ParentComponent() {
  return (
    <Router basename='/app'>
      <h1>Media</h1>

      <nav>
        <Link to="/">Home</Link>&nbsp;
        <a href="http://novell.mause.me:9091" target="_blank">Transmission</a>&nbsp;
        <a href="https://app.plex.tv" target="_blank">Plex</a>&nbsp;
        <a href="/user/sign-out">Logout</a>
      </nav>

      <br />

      <Switch>
        <RouteWithTitle path="/select/:tmdb_id/options" title="Movie Options"><OptionsComponent type='movie' /></RouteWithTitle>
        <RouteWithTitle path="/select/:tmdb_id/season/:season/episode/:episode/options" title="TV Options"><OptionsComponent type='series' /></RouteWithTitle>
        <RouteWithTitle path="/select/:tmdb_id/season/:season" title="Select Episode"><EpisodeSelectComponent /></RouteWithTitle>
        <RouteWithTitle path="/select/:tmdb_id/season" title="Select Season"><SeasonSelectComponent /></RouteWithTitle>
        <RouteWithTitle path="/search" title="Search"><SearchComponent /></RouteWithTitle>
        <RouteWithTitle path="/download" title="Download"><DownloadComponent /></RouteWithTitle>
        <RouteWithTitle path="/stats" title="Stats"><StatsComponent /></RouteWithTitle>
        <RouteWithTitle path="/" title="Media"><IndexComponent /></RouteWithTitle>
      </Switch>
    </Router>
  );
}

ReactDOM.render(<ParentComponent />, document.getElementById('app'));
