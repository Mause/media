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
import { EpisodeSelectComponent, Season, SeasonSelectComponent } from './SeasonSelectComponent';
import { load, subscribe, useLoad } from './utils';
import Axios from 'axios';
import { StatsComponent } from './StatsComponent';

Sentry.init({
  dsn: "https://8b67269f943a4e3793144fdc31258b46@sentry.io/1869914",
  release: process.env.HEROKU_SLUG_COMMIT,
  environment: process.env.NODE_ENV === 'production' ? 'production' : 'development',
});

const ranking = [
  'Movies/XVID',
  'Movies/x264',
  'Movies/x264/720',
  'Movies/XVID/720',
  'Movies/BD Remux',
  'Movies/Full BD',
  'Movies/x264/1080',
  'Movies/x264/4k',
  'Movies/x265/4k',
  'Movies/x264/3D',
  'Movs/x265/4k/HDR',

  'TV Episodes',
  'TV HD Episodes',
  'TV UHD Episodes',
  'TV-UHD-episodes',
];

interface ITorrent {
  title: string;
  seeders: number;
  download: string;
}
type OptionsProps = { type: 'movie' | 'series' } & RouteComponentProps<{ tmdb_id: string, season?: string, episode?: string }>;

interface ItemInfo {
  imdb_id: string;
  title: string;
}

function getHash(magnet: string) {
  const u = new URL(magnet);
  return _.last(u.searchParams.get('xt')!.split(':'))
}

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

function DisplayTorrent({ torrent, torrents, itemInfo, type }: { torrent: ITorrent, torrents?: Torrents, itemInfo?: ItemInfo, type: string }) {
  let url;
  if (itemInfo) {
    url = {
      pathname: `/download`, state: {
        type,
        imdb_id: itemInfo.imdb_id,
        magnet: torrent.download,
        titles: itemInfo.title,
      }
    };
  }
  return (
    <span>
      {url ? <Link to={url}>{torrent.title}</Link> : torrent.title}
      &nbsp;
      <small>{torrent.seeders}</small>
      &nbsp;
      {torrents && getHash(torrent.download)! in torrents ? <small>downloaded</small> : ''}
    </span>
  );
}
function remove(bit: string): string {
  if (bit.startsWith('Mov')) {
    const parts = bit.split('/');
    return parts.slice(1).join('/');
  }
  return bit;
}

class _OptionsComponent extends Component<
  OptionsProps,
  { results: ITorrent[], torrents?: Torrents, loading: boolean, itemInfo?: ItemInfo }
  > {
  constructor(props: OptionsProps) {
    super(props);
    this.state = { results: [], loading: true, itemInfo: undefined };
  }
  public render() {
    const dt = (result: ITorrent) => <DisplayTorrent itemInfo={this.state.itemInfo} type={type} torrents={this.state.torrents} torrent={result} />
    const { type } = this.props;
    const grouped = _.groupBy(this.state.results, 'category');
    const auto = _.maxBy(grouped['Movies/x264/1080'] || grouped['TV HD Episodes'] || [], 'seeders');
    const bits = _.sortBy(
      _.toPairs(grouped),
      ([category]) => -ranking.indexOf(category),
    ).map(([category, results]) => (
      <div key={category}>
        <h3>{remove(category)}</h3>
        {_.sortBy(results, i => -i.seeders).map(result => (
          <li key={result.title}>{dt(result)}</li>
        ))}
      </div>
    ));
    return (
      <div>
        {this.state.loading ? <i className="fas fa-spinner fa-spin fa-xs"></i> : ''}
        {
          bits.length || this.state.loading ?
            <div>
              <p>
                Auto selection: {auto ? dt(auto) : 'None'}
              </p>
              <ul>{bits}</ul>
            </div> :
            'No results'
        }
      </div>
    );
  }
  componentDidMount() {
    const { tmdb_id, season, episode } = this.props.match.params;

    load<Torrents>('torrents').then(torrents => this.setState({ torrents }));

    const prom = load<ItemInfo>(`${this.props.type == 'series' ? 'tv' : 'movie'}/${tmdb_id}`);
    if (this.props.type === 'series') {
      Promise.all([
        load<Season>(`tv/${tmdb_id}/season/${season}`),
        prom]).then(([season, { imdb_id }]) => {
          this.setState({ itemInfo: { title: season.episodes[parseInt(episode!, 10)].name, imdb_id } });
        })
    } else {
      prom.then(itemInfo => this.setState({ itemInfo }));
    }
    subscribe(
      `/stream/${this.props.type}/${tmdb_id}?` + qs.stringify({ season, episode }),
      data => {
        this.setState(state => ({
          ...state,
          results: state.results.concat([data]),
        }));
      },
      () => this.setState({ loading: false }),
    );
  }
}
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

interface SearchResult {
  Type: string,
  Year: number,
  imdbID: number,
  title: string
}

function getQuery(props: RouteComponentProps<{}>) {
  return qs.parse(props.location.search.slice(1)).query;
}

const SearchComponent = withRouter(function SearchComponent(props: RouteComponentProps<{}>) {
  const results = useLoad<SearchResult[]>(
    'search',
    { query: getQuery(props) }
  );
  return <div>
    <ul>
      {results ? results.map(result =>
        <li key={result.imdbID}>
          <Link to={
            result.Type === 'movie' ?
              `/select/${result.imdbID}/options` :
              `/select/${result.imdbID}/season`}>{result.title} ({result.Year ? result.Year : 'Unknown year'})</Link>
        </li>
      ) : <ReactLoading type='balls' color='#000' />}
    </ul>
    {results && results.length === 0 ?
      'No results' : null}
  </div>
});

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

const OptionsComponent = withRouter(_OptionsComponent);
ReactDOM.render(<ParentComponent />, document.getElementById('app'));
