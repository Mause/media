import * as Sentry from '@sentry/browser';
import Axios from 'axios';
import _ from 'lodash';
import qs from 'qs';
import React, { Component, useState } from 'react';
import ReactDOM from 'react-dom';
import Helmet from 'react-helmet';
import { RouteProps } from 'react-router';
import { BrowserRouter as Router, Link, Route, RouteComponentProps, Switch, withRouter } from 'react-router-dom';
import { IndexComponent } from './IndexComponent';
import { load, subscribe } from './utils';
import ReactLoading from 'react-loading';

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
type IAppProps = {} & RouteComponentProps<{ tmdb_id: string }>;

interface ItemInfo {
  imdb_id: string;
  title: string;
}

function DisplayTorrent({ torrent, itemInfo }: { torrent: ITorrent, itemInfo: Promise<ItemInfo> }) {
  const [url, setUrl] = useState<string>();
  itemInfo.then(data => {
    setUrl(
      '/download/movie?' +
      qs.stringify({
        imdb_id: data.imdb_id,
        magnet: torrent.download,
        titles: data.title,
      }));
  })
  return (
    <span>
      <a href={url}>{torrent.title}</a>
      &nbsp;
      <small>{torrent.seeders}</small>
    </span>
  );
}
function remove(bit: string): string {
  const parts = bit.split('/');
  return parts.slice(1).join('/');
}

class AppComponent extends Component<
  IAppProps,
  { results: ITorrent[]; loading: boolean }
  > {
  itemInfo: Promise<ItemInfo>;
  constructor(props: IAppProps) {
    super(props);
    this.state = { results: [], loading: true };
    this.onComponentMount();
    this.itemInfo = Axios.get<ItemInfo>(`/api/movie/${props.match.params.tmdb_id}`).then(({ data }) => data);
  }
  public render() {
    const grouped = _.groupBy(this.state.results, 'category');
    const auto = _.maxBy(grouped['Movies/x264/1080'] || [], 'seeders');
    const bits = _.sortBy(
      _.toPairs(grouped),
      ([category]) => -ranking.indexOf(category),
    ).map(([category, results]) => (
      <div key={category}>
        <h3>{remove(category)}</h3>
        {_.sortBy(results, i => -i.seeders).map(result => (
          <li key={result.title}>
            <DisplayTorrent torrent={result} itemInfo={this.itemInfo} />
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
                Auto selection: {auto ? <DisplayTorrent torrent={auto} itemInfo={this.itemInfo} /> : 'None'}
              </p>
              <ul>{bits}</ul>
            </div> :
            'No results'
        }
      </div>
    );
  }
  private onComponentMount() {
    const { tmdb_id } = this.props.match.params;
    subscribe(
      `/select/${tmdb_id}/options/stream`,
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
    {
      download: Download,
      episode: number,
      id: number,
      season: number,
      show_title: string;
    }[]
  };
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
      <Route {...props} />
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
      results => this.setState({ results }),
      { query: this.getQuery() }
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
        <a href="http://novell.mause.me:32400" target="_blank">Plex</a>&nbsp;
        <a href="/user/sign-out">Logout</a>
      </nav>

      <br />

      <Switch>
        <RouteWithTitle path="/select/:tmdb_id/options" title="Options"><Wrapped /></RouteWithTitle>
        <RouteWithTitle path="/search" title="Search"><SearchComponent /></RouteWithTitle>
        <RouteWithTitle path="/" title="Media"><IndexComponent /></RouteWithTitle>
      </Switch>
    </Router>
  );
}

const Wrapped = withRouter(AppComponent);
ReactDOM.render(<ParentComponent />, document.getElementById('app'));
