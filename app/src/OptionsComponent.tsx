import _ from 'lodash';
import qs from 'qs';
import React, { useState, useEffect } from 'react';
import { subscribe, MLink } from './utils';
import { Torrents } from './streaming';
import { useParams } from 'react-router-dom';
import useSWR from 'swr';
import { Loading } from './render';
import { Breadcrumbs, Typography } from '@material-ui/core';
import { Shared } from './SeasonSelectComponent';
import { DownloadState } from './DownloadComponent';
import { DisplayError } from './IndexComponent';

function getHash(magnet: string) {
  const u = new URL(magnet);
  return _.last(u.searchParams.get('xt')!.split(':'));
}

export interface ITorrent {
  source: 'KICKASS' | 'RARBG' | 'HORRIBLESUBS';
  title: string;
  seeders: number;
  download: string;
  category: string;
  episode_info: { seasonnum?: string; epnum?: string };
}

export function DisplayTorrent({
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
  const state: DownloadState = {
    downloads: [
      {
        tmdb_id: tmdb_id,
        magnet: torrent.download,
        season: season,
        episode: episode,
      },
    ],
  };
  const url = { pathname: '/download', state };
  return (
    <span>
      <strong title={torrent.source}>{torrent.source.substring(0, 1)}</strong>
      &nbsp;
      <MLink to={url}>{torrent.title}</MLink>
      &nbsp;
      <small>{torrent.seeders}</small>
      &nbsp;
      {torrents && getHash(torrent.download)! in torrents && (
        <small>downloaded</small>
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
  const { data: torrents } = useSWR<Torrents>('torrents');
  const { items: results, loading, error } = useSubscribe<ITorrent>(
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
      {_.sortBy(results, (i) => -i.seeders).map((result) => (
        <li key={result.title}>{dt(result)}</li>
      ))}
    </div>
  ));

  let header = null;
  if (type === 'movie') {
    header = (
      <Breadcrumbs aria-label="breadcrumb">
        <Shared />
        <Typography color="textPrimary">{meta && meta.title}</Typography>
      </Breadcrumbs>
    );
  } else {
    const url = `/select/${tmdb_id}/season`;
    header = (
      <Breadcrumbs aria-label="breadcrumb">
        <Shared />
        <MLink color="inherit" to={url}>
          {meta && meta.title}
        </MLink>
        <MLink color="inherit" to={`${url}/${season}`}>
          Season {season}
        </MLink>
        <Typography color="textPrimary">Episode {episode}</Typography>
      </Breadcrumbs>
    );
  }

  return (
    <div>
      {header}
      <div style={{ textAlign: 'center' }}>
        <Loading loading={loading} large={true} />
      </div>
      {error && <DisplayError error={error} />}
      {bits.length || loading ? (
        <div>
          <p>Auto selection: {auto ? dt(auto) : 'None'}</p>
          <ul>{bits}</ul>
        </div>
      ) : (
        <div>
          <p>No results</p>
        </div>
      )}
      <ul>
        <li>
          <MLink
            to={{
              pathname: '/manual',
              state: { tmdb_id, season, episode },
            }}
          >
            Add manually
          </MLink>
        </li>
        <li>
          <MLink
            to={{
              pathname: `/monitor/add/${tmdb_id}`,
              state: { type: type === 'movie' ? 'MOVIE' : 'TV' },
            }}
          >
            Add to monitor
          </MLink>
        </li>
      </ul>
    </div>
  );
}

function useSubscribe<T>(url: string) {
  const [subscription, setSubscription] = useState<{
    items: T[];
    loading: boolean;
    error?: Error;
  }>({ loading: true, items: [], error: undefined });

  useEffect(() => {
    const items: T[] = [];
    subscribe<T>(
      url,
      (data) => {
        items.push(data);
        setSubscription({
          items,
          loading: true,
        });
      },
      (error) => setSubscription({ error, loading: false, items }),
      () => setSubscription({ loading: false, items }),
    );
  }, [url]);

  return subscription;
}

export { OptionsComponent };
