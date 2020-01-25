import _ from 'lodash';
import qs from 'qs';
import React, { Component } from 'react';
import { Season } from './SeasonSelectComponent';
import { load, subscribe } from './utils';
import { Torrents } from './streaming';
import { withRouter, RouteComponentProps, Link } from 'react-router-dom';

type OptionsProps = { type: 'movie' | 'series' } & RouteComponentProps<{ tmdb_id: string, season?: string, episode?: string }>;


function getHash(magnet: string) {
  const u = new URL(magnet);
  return _.last(u.searchParams.get('xt')!.split(':'))
}

interface ITorrent {
  title: string;
  seeders: number;
  download: string;
}

interface ItemInfo {
  imdb_id: string;
  title: string;
}

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

function remove(bit: string): string {
  if (bit.startsWith('Mov')) {
    const parts = bit.split('/');
    return parts.slice(1).join('/');
  }
  return bit;
}

class _OptionsComponent extends Component<OptionsProps, {
  results: ITorrent[];
  torrents?: Torrents;
  loading: boolean;
  itemInfo?: ItemInfo;
}> {
  constructor(props: OptionsProps) {
    super(props);
    this.state = { results: [], loading: true, itemInfo: undefined };
  }
  public render() {
    const dt = (result: ITorrent) => <DisplayTorrent itemInfo={this.state.itemInfo} type={type} torrents={this.state.torrents} torrent={result} />;
    const { type } = this.props;
    const grouped = _.groupBy(this.state.results, 'category');
    const auto = _.maxBy(grouped['Movies/x264/1080'] || grouped['TV HD Episodes'] || [], 'seeders');
    const bits = _.sortBy(_.toPairs(grouped), ([category]) => -ranking.indexOf(category)).map(([category, results]) => (<div key={category}>
      <h3>{remove(category)}</h3>
      {_.sortBy(results, i => -i.seeders).map(result => (<li key={result.title}>{dt(result)}</li>))}
    </div>));
    return (<div>
      {this.state.loading ? <i className="fas fa-spinner fa-spin fa-xs"></i> : ''}
      {bits.length || this.state.loading ?
        <div>
          <p>
            Auto selection: {auto ? dt(auto) : 'None'}
          </p>
          <ul>{bits}</ul>
        </div> :
        'No results'}
    </div>);
  }
  componentDidMount() {
    const { tmdb_id, season, episode } = this.props.match.params;
    load<Torrents>('torrents').then(torrents => this.setState({ torrents }));
    const prom = load<ItemInfo>(`${this.props.type == 'series' ? 'tv' : 'movie'}/${tmdb_id}`);
    if (this.props.type === 'series') {
      Promise.all([
        load<Season>(`tv/${tmdb_id}/season/${season}`),
        prom
      ]).then(([season, { imdb_id }]) => {
        this.setState({ itemInfo: { title: season.episodes[parseInt(episode!, 10)].name, imdb_id } });
      });
    }
    else {
      prom.then(itemInfo => this.setState({ itemInfo }));
    }
    subscribe(`/stream/${this.props.type}/${tmdb_id}?` + qs.stringify({ season, episode }), data => {
      this.setState(state => ({
        ...state,
        results: state.results.concat([data]),
      }));
    }, () => this.setState({ loading: false }));
  }
}

const OptionsComponent = withRouter(_OptionsComponent);
export { OptionsComponent };
