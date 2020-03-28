import { useParams } from 'react-router-dom';
import useSWR from 'swr';
import { ITorrent, DisplayTorrent } from './OptionsComponent';
import React from 'react';
import { Loading } from './render';
import { EpisodeSelectBreadcrumbs } from './SeasonSelectComponent';
import { MLink } from './utils';
import { DownloadCall } from './DownloadComponent';
import { Torrents } from './streaming';

type MapType = [string, ITorrent[]][];

function DownloadAllComponent() {
  const { tmdb_id, season } = useParams<{ tmdb_id: string; season: string }>();

  const { data: torrents } = useSWR<Torrents>('torrents');
  const { data, isValidating } = useSWR<{
    packs: ITorrent[];
    complete: MapType;
    incomplete: MapType;
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
                <DisplayTorrent
                  torrents={torrents}
                  torrent={t}
                  tmdb_id={tmdb_id}
                  season={season}
                />
              </li>
            ))}
        </ul>
      </div>
      <Individual
        label="Complete Sets"
        items={data && data.complete}
        season={season}
        tmdb_id={tmdb_id}
        torrents={torrents}
      />
      <Individual
        label="Incomplete Sets"
        items={data && data.incomplete}
        season={season}
        tmdb_id={tmdb_id}
        torrents={torrents}
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
  items?: MapType;
  season: string;
  tmdb_id: string;
  torrents?: Torrents;
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
                      torrents={props.torrents}
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
