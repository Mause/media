import { useParams } from 'react-router-dom';
import useSWR from 'swr';
import { ITorrent, DisplayTorrent } from './OptionsComponent';
import React from 'react';
import { Loading } from './render';
import { EpisodeSelectBreadcrumbs } from './SeasonSelectComponent';
import { MLink } from './utils';
import { DownloadCall } from './DownloadComponent';

type T = [string, ITorrent[]][];

function DownloadAllComponent() {
  const { tmdb_id, season } = useParams<{ tmdb_id: string; season: string }>();

  const { data, isValidating } = useSWR<{
    packs: ITorrent[];
    complete: T;
    incomplete: T;
  }>(`select/${tmdb_id}/season/${season}/download_all`);

  return (
    <div>
      <EpisodeSelectBreadcrumbs tmdb_id={tmdb_id} season={season} />
      <Loading loading={isValidating} />
      <div>
        <h3>Packs</h3>
        <ul>
          {data &&
            data.packs &&
            data.packs.map(t => (
              <li key={t.download}>
                <DisplayTorrent torrent={t} tmdb_id={tmdb_id} season={season} />
              </li>
            ))}
        </ul>
      </div>
      <Individual
        label="Complete Sets"
        items={data && data.complete}
        season={season}
        tmdb_id={tmdb_id}
      />
      <Individual
        label="Incomplete Sets"
        items={data && data.incomplete}
        season={season}
        tmdb_id={tmdb_id}
      />
    </div>
  );
}

function download_all(tmdb_id: string, torrents: ITorrent[]) {
  const downloads: DownloadCall[] = torrents.map(t => ({
    tmdb_id,
    magnet: t.download,
    season: t.episode_info.seasonnum,
    episode: t.episode_info.epnum,
  }));

  return { pathname: '/download', state: { downloads } };
}

function Individual(props: {
  label: string;
  items?: T;
  season: string;
  tmdb_id: string;
}) {
  return (
    <div>
      <h3>{props.label}</h3>
      <ul>
        {props.items &&
          props.items.map(([name, torrents]) => (
            <div key={name}>
              <h4>
                <MLink to={download_all(props.tmdb_id, torrents)}>{name}</MLink>
              </h4>
              <ul>
                {torrents.map(t => (
                  <li key={t.download}>
                    <DisplayTorrent
                      torrent={t}
                      tmdb_id={props.tmdb_id}
                      season={props.season}
                      episode={t.episode_info.epnum}
                    />
                  </li>
                ))}
              </ul>
            </div>
          ))}
      </ul>
    </div>
  );
}

export { DownloadAllComponent };
