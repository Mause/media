import _ from 'lodash';
import qs from 'qs';
import React, { useState, useEffect } from 'react';
import { subscribe, useLoad } from './utils';
import { Torrents } from './streaming';
import { Link, useParams } from 'react-router-dom';
import useSWR from 'swr';
import { getMarker } from './render';

function getHash(magnet: string) {
  const u = new URL(magnet);
  return _.last(u.searchParams.get('xt')!.split(':'));
}

export interface ITorrent {
  title: string;
  seeders: number;
  download: string;
  category: string;
}

function DisplayTorrent({
  torrent,
  torrents,
  tmdb_id,
  season,
  episode,
}: {
  season?: string;
  episode?: string;
  tmdb_id: string;
  torrent: ITorrent;
  torrents?: Torrents;
}) {
  let url = {
    pathname: `/download`,
    state: {
      tmdb_id: tmdb_id,
      magnet: torrent.download,
      season: season,
      episode: episode,
    },
  };
  return (
    <span>
      <Link to={url}>{torrent.title}</Link>
      &nbsp;
      <small>{torrent.seeders}</small>
      &nbsp;
      {torrents && getHash(torrent.download)! in torrents ? (
        <small>downloaded</small>
      ) : (
        ''
      )}
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

function OptionsComponent({ type }: { type: 'movie' | 'series' }) {
  const { season, episode, tmdb_id } = useParams<{
    tmdb_id: string;
    season?: string;
    episode?: string;
  }>();

  const { data: meta } = useSWR<{ title: string }>(
    (season ? 'tv' : 'movie') + '/' + tmdb_id,
  );
  const torrents = useLoad<Torrents>('torrents');
  const { items: results, loading } = useSubscribe<ITorrent>(
    `/stream/${type}/${tmdb_id}?` + qs.stringify({ season, episode }),
  );
  const dt = (result: ITorrent) => (
    <DisplayTorrent
      tmdb_id={tmdb_id}
      season={season}
      episode={episode}
      torrents={torrents}
      torrent={result}
    />
  );
  const grouped = _.groupBy(results, 'category');
  const auto = _.maxBy(
    grouped['Movies/x264/1080'] || grouped['TV HD Episodes'] || [],
    'seeders',
  );
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
      <h3>
        {meta && meta.title} {season && getMarker({ season, episode })}
      </h3>
      {loading ? <i className="fas fa-spinner fa-spin fa-xs" /> : ''}
      {bits.length || loading ? (
        <div>
          <p>Auto selection: {auto ? dt(auto) : 'None'}</p>
          <ul>{bits}</ul>
        </div>
      ) : (
        <div>
          No results
          <ul>
            <li>
              <Link to={{ pathname: '/manual' }}>Add manually</Link>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}

function useSubscribe<T>(url: string) {
  const [subscription, setSubscription] = useState<{
    items: T[];
    loading: boolean;
  }>({ loading: true, items: [] });

  useEffect(() => {
    const items: T[] = [];
    subscribe(
      url,
      data => {
        items.push(data);
        setSubscription({
          items,
          loading: true,
        });
      },
      () => setSubscription({ loading: false, items }),
    );
  }, [url]);

  return subscription;
}

export { OptionsComponent };
