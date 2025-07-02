import * as _ from 'lodash-es';

import { Torrents } from './streaming';
import { DownloadState } from './DownloadComponent';
import { MLink } from './MLink';
import { ITorrent } from './OptionsComponent';

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
