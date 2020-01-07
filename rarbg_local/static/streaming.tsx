import * as Sentry from '@sentry/browser';
import _ from 'lodash';
import qs from 'qs';
import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import Helmet from 'react-helmet';
import ReactLoading from 'react-loading';
import { RouteProps } from 'react-router';
import { BrowserRouter as Router, Link, Route, RouteComponentProps, Switch, withRouter } from 'react-router-dom';
import { IndexComponent } from './IndexComponent';
import { EpisodeSelectComponent, Season, SeasonSelectComponent } from './SeasonSelectComponent';
import { load, subscribe } from './utils';

Sentry.init({ dsn: "https://8b67269f943a4e3793144fdc31258b46@sentry.io/1869914" });

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

function DisplayTorrent({ torrent, itemInfo, type }: { torrent: ITorrent, itemInfo?: ItemInfo, type: string }) {
  let url;
  if (itemInfo) {
    url = `/download/${type}?` +
      qs.stringify({
        imdb_id: itemInfo.imdb_id,
        magnet: torrent.download,
        titles: itemInfo.title,
      });
  }
  return (
    <span>
      <a href={url}>{torrent.title}</a>
      &nbsp;
      <small>{torrent.seeders}</small>
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
  { results: ITorrent[]; loading: boolean, itemInfo?: ItemInfo }
  > {
  constructor(props: OptionsProps) {
    super(props);
    this.state = { results: [], loading: true, itemInfo: undefined };
  }
  public render() {
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
          <li key={result.title}>
            <DisplayTorrent torrent={result} itemInfo={this.state.itemInfo} type={type} />
          </li>
        ))}
      </div>
    ));
    return (
      <div>
        {this.state.loading ? 'Loading...' : ''}
        {
          bits.length || this.state.loading ?
            <div>
              <p>
                Auto selection: {auto ? <DisplayTorrent torrent={auto} itemInfo={this.state.itemInfo} type={type} /> : 'None'}
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
}
export interface MovieResponse {
  download: Download,
  id: number
}
export interface SeriesResponse {
  imdb_id: string;
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

const SearchComponent = withRouter(class SearchComponent extends Component<RouteComponentProps<{}>, { results?: SearchResult[] }>{
  constructor(props: RouteComponentProps<{}>) {
    super(props);
    this.state = {};
  }
  getQuery() {
    return qs.parse(this.props.location.search.slice(1)).query;
  }
  componentDidMount() {
    load<SearchResult[]>(
      'search',
      { query: this.getQuery() }
    ).then(
      results => this.setState({ results })
    );
  }
  render() {
    return <div>
      <ul>
        {this.state.results ? this.state.results.map(result =>
          <li key={result.imdbID}>
            <Link to={
              result.Type === 'movie' ?
                `/select/${result.imdbID}/options` :
                `/select/${result.imdbID}/season`}>{result.title} ({result.Year ? result.Year : 'Unknown year'})</Link>
          </li>
        ) : <ReactLoading type='balls' color='#000' />}
      </ul>
    </div>
  }
});

function ParentComponent() {
  return (
    <Router basename='/app'>
      <h1>Media</h1>

      <nav>
        <Link to="/">Home</Link>&nbsp;
        <a href="http://novell.mause.me:9091" target="_blank">Transmission</a>&nbsp;
        <a href="https://app.plex.com" target="_blank">Plex</a>&nbsp;
        <a href="/user/sign-out">Logout</a>
      </nav>

      <br />

      <Switch>
        <RouteWithTitle path="/select/:tmdb_id/options" title="Movie Options"><OptionsComponent type='movie' /></RouteWithTitle>
        <RouteWithTitle path="/select/:tmdb_id/season/:season/episode/:episode/options" title="TV Options"><OptionsComponent type='series' /></RouteWithTitle>
        <RouteWithTitle path="/select/:tmdb_id/season/:season" title="Select Episode"><EpisodeSelectComponent /></RouteWithTitle>
        <RouteWithTitle path="/select/:tmdb_id/season" title="Select Season"><SeasonSelectComponent /></RouteWithTitle>
        <RouteWithTitle path="/search" title="Search"><SearchComponent /></RouteWithTitle>
        <RouteWithTitle path="/" title="Media"><IndexComponent /></RouteWithTitle>
      </Switch>
    </Router>
  );
}

const OptionsComponent = withRouter(_OptionsComponent);
ReactDOM.render(<ParentComponent />, document.getElementById('app'));
