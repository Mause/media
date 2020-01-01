import _ from 'lodash';
import qs from 'qs';
import Axios from 'axios';
import React, { useState } from 'react';
import { Component } from 'react';
import ReactDOM from 'react-dom';
import { HashRouter, withRouter, RouteComponentProps } from 'react-router-dom';
import { subscribe } from './subscribe';

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
      ([category, results]) => -ranking.indexOf(category),
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
        <p>
          Auto selection: {auto ? <DisplayTorrent torrent={auto} itemInfo={this.itemInfo} /> : 'None'}
        </p>
        <ul>{bits}</ul>
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


const Wrapped = withRouter(AppComponent);
ReactDOM.render( <HashRouter><Wrapped /></HashRouter>, document.getElementById('app'));
