import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useSWR from 'swr';
import { Breadcrumbs, Typography, Alert } from '@mui/material';
import { useAuth0 } from '@auth0/auth0-react';
import * as _ from 'lodash-es';

import * as qs from './qs';
import { subscribe, MLink, getToken } from './utils';
import type { Torrents } from './streaming';
import { Loading } from './render';
import { Shared } from './SeasonSelectComponent';
import type { DownloadState } from './DownloadComponent';
import { DisplayError } from './IndexComponent';
import type { components } from './schema';
import { MonitorAddComponent } from './MonitorComponent';

export type ITorrent = components['schemas']['ITorrent'];
type ProviderSource = components['schemas']['ProviderSource'];

function getHash(magnet: string) {
  const u = new URL(magnet);
  return _.last(u.searchParams.get('xt')!.split(':'));
}

export function DisplayTorrent({
  torrent,
  torrents,
  tmdb_id,
  season,
  episode,
}: {
  season?: number;
  episode?: number | null;
  tmdb_id: string;
  torrent: ITorrent;
  torrents?: Torrents;
}) {
  const state: DownloadState = {
    downloads: [
      {
        tmdb_id: parseInt(tmdb_id),
        magnet: torrent.download,
        season: season,
        episode: episode,
      },
    ],
  };
  const url = { to: '/download', state };
  return (
    <span>
      <strong title={torrent.source}>
        {torrent.source.substring(0, 1).toUpperCase()}
      </strong>
      &nbsp;
      <MLink {...url}>{torrent.title}</MLink>
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
  const { season, episode, tmdb_id } = useParams();

  const { data: meta } = useSWR<{ title: string }>(
    (season ? 'tv' : 'movie') + '/' + tmdb_id,
  );
  const { data: torrents } = useSWR<Torrents>('torrents');
  const {
    items: results,
    loading,
    errors,
  } = useSubscribes<ITorrent>(
    `/api/stream/${type}/${tmdb_id}?` + qs.stringify({ season, episode }),
  );
  const dt = (result: ITorrent) => (
    <DisplayTorrent
      tmdb_id={tmdb_id!}
      season={parseInt(season!)}
      episode={parseInt(episode!)}
      torrents={torrents}
      torrent={result}
    />
  );
  const grouped = _.groupBy(results, 'category');
  const auto = _.maxBy(
    grouped['x264/1080'] || grouped['TV HD Episodes'] || [],
    'seeders',
  );
  const bits = _.sortBy(
    Object.entries(grouped),
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
        <Loading loading={loading.length !== 0} large={true} />
      </div>
      {Object.entries(errors).map(([key, error]) => (
        <DisplayError
          key={key}
          message={`Error occured whilst loading options from ${key}`}
          error={error}
        />
      ))}
      {loading.map((source) => (
        <Alert key={source} color="info">
          Loading options from {source}
        </Alert>
      ))}
      {bits.length || loading.length !== 0 ? (
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
          <MLink to="/manual" state={{ tmdb_id, season, episode }}>
            Add manually
          </MLink>
        </li>
        <li>
          <MonitorAddComponent
            tmdb_id={parseInt(tmdb_id!)}
            type={type === 'movie' ? 'MOVIE' : 'TV'}
          />
        </li>
        <li>
          <MLink
            to={{
              pathname: `/websocket/${tmdb_id}`,
              search: qs.stringify({ season, episode }),
            }}
          >
            Search with websockets
          </MLink>
        </li>
      </ul>
    </div>
  );
}

interface SubscriptionShape<T> {
  items: T[];
  name: string;
  loading: boolean;
  error?: Error;
}

function useSubscribe<T>(
  baseUrl: string,
  name: string,
  authorization?: string,
): SubscriptionShape<T> {
  const url = baseUrl + '&source=' + name;
  const [subscription, setSubscription] = useState<SubscriptionShape<T>>({
    items: [],
    loading: true,
    name,
    error: undefined,
  });

  useEffect(() => {
    if (!authorization) return; // don't subscribe until we have auth

    const items: T[] = [];
    return subscribe<T>(
      url,
      (data) => {
        items.push(data);
        setSubscription({
          items,
          name,
          loading: true,
        });
      },
      (error) => setSubscription({ name, error, loading: false, items }),
      authorization,
      () => setSubscription({ name, loading: false, items }),
    );
  }, [url, authorization, name]);

  return subscription;
}

function useToken() {
  const auth = useAuth0();
  const [token, setToken] = useState<string>();
  useEffect(() => {
    void getToken(auth).then(setToken);
  }, [auth]);
  return token;
}

function useSubscribes<T>(url: string): {
  items: T[];
  loading: string[];
  errors: { [key: string]: Error };
} {
  const token = useToken();

  const p: ProviderSource[] = [
    /*
    'rarbg',
    'horriblesubs',
    'kickass',
    */
    'torrentscsv',
    'nyaasi',
    'piratebay',
  ];
  const providers = [
    useSubscribe<T>(url, p[0], token),
    useSubscribe<T>(url, p[1], token),
    useSubscribe<T>(url, p[2], token),
    /*
    useSubscribe<T>(url, p[3], token),
    useSubscribe<T>(url, p[4], token),
    useSubscribe<T>(url, p[5], token),
    */
  ];

  return {
    items: providers
      .map((t) => t.items || [])
      .reduce((a, b) => a.concat(b), []),
    loading: providers.filter((t) => t.loading).map((t) => t.name),
    errors: Object.fromEntries(
      providers.filter((t) => t.error).map((t, i) => [p[i], t.error]),
    ) as { [key: string]: Error },
  };
}

export { OptionsComponent };
