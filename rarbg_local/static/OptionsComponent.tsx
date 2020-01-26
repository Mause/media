import _ from 'lodash';
import qs from 'qs';
import React, { Component, useState, useEffect } from 'react';
import { Season } from './SeasonSelectComponent';
import { load, subscribe, useLoad } from './utils';
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
  loading: boolean;
  itemInfo?: ItemInfo;
}> {
  constructor(props: OptionsProps) {
    super(props);
    this.state = { results: [], loading: true, itemInfo: undefined };
  }
  public render() {
    return <Pure
      itemInfo={this.state.itemInfo}
      type={this.props.type}
      episode={this.props.match.params.episode}
      season={this.props.match.params.season}
      tmdb_id={this.props.match.params.tmdb_id}
    />;
  }
  componentDidMount() {
    const { tmdb_id, season, episode } = this.props.match.params;
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
  }
}

function Pure(props: { itemInfo?: ItemInfo, type: string, tmdb_id: string, season?: string, episode?: string }) {
  const torrents = useLoad<Torrents>('torrents');
  const { type } = props;
  const { items: results, loading } = useSubscribe<ITorrent>(`/stream/${type}/${props.tmdb_id}?` + qs.stringify({ season: props.season, episode: props.episode }));
  const dt = (result: ITorrent) => <DisplayTorrent itemInfo={props.itemInfo} type={type} torrents={torrents} torrent={result} />;
  const grouped = _.groupBy(results, 'category');
  const auto = _.maxBy(grouped['Movies/x264/1080'] || grouped['TV HD Episodes'] || [], 'seeders');
  const bits = _.sortBy(_.toPairs(grouped), ([category]) => -ranking.indexOf(category)).map(([category, results]) => (<div key={category}>
    <h3>{remove(category)}</h3>
    {_.sortBy(results, i => -i.seeders).map(result => (<li key={result.title}>{dt(result)}</li>))}
  </div>));
  return (<div>
    {loading ? <i className="fas fa-spinner fa-spin fa-xs"></i> : ''}
    {bits.length || loading ?
      <div>
        <p>
          Auto selection: {auto ? dt(auto) : 'None'}
        </p>
        <ul>{bits}</ul>
      </div> :
      'No results'}
  </div>);
}

function useSubscribe<T>(url: string) {
  const [subscription, setSubscription] = useState<{ items: T[], loading: boolean }>({ loading: true, items: [] });

  useEffect(() => {
    const items: T[] = [];
    subscribe(url, data => {
      items.push(data);
      setSubscription({
        items,
        loading: true,
      })
    }, () => setSubscription({ loading: false, items }));
  }, [url]);

  return subscription;
}


const OptionsComponent = withRouter(_OptionsComponent);
export { OptionsComponent };
