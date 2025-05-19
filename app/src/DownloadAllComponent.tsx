import { useParams } from 'react-router-dom';
import useSWR from 'swr';
import { ITorrent, DisplayTorrent } from './OptionsComponent';
import React from 'react';
import { Loading } from './render';
import { EpisodeSelectBreadcrumbs } from './SeasonSelectComponent';
import { MLink } from './utils';
import { DownloadCall } from './DownloadComponent';
import { Torrents } from './streaming';
import { DisplayError } from './IndexComponent';

type MapType = [string, ITorrent[]][];

function DownloadAllComponent() {
  const { tmdb_id, season: season_s } = useParams<{
    tmdb_id: string;
    season: string;
  }>();
  const season = parseInt(season_s!);

  const { data: torrents } = useSWR<Torrents>('torrents');
  const { data, isValidating, error } = useSWR<
    {
      packs: ITorrent[];
      complete: MapType;
      incomplete: MapType;
    },
    Error
  >(`select/${tmdb_id}/season/${season}/download_all`);

  return (
    <div>
      {error && <DisplayError error={error} />}
      <EpisodeSelectBreadcrumbs tmdb_id={tmdb_id!} season={season} />
      <Loading loading={isValidating} />
      <div>
        <h3>Packs</h3>
        <ul>
          {data &&
            data.packs &&
            data.packs.map((t) => (
              <li key={t.download}>
                <DisplayTorrent
                  torrents={torrents}
                  torrent={t}
                  tmdb_id={tmdb_id!}
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
        tmdb_id={tmdb_id!}
        torrents={torrents}
      />
      <Individual
        label="Incomplete Sets"
        items={data && data.incomplete}
        season={season}
        tmdb_id={tmdb_id!}
        torrents={torrents}
      />
    </div>
  );
}

function download_all(tmdb_id: number, torrents: ITorrent[]) {
  const downloads: DownloadCall[] = torrents.map((t) => ({
    tmdb_id,
    magnet: t.download,
    season: t.episode_info?.seasonnum,
    episode: t.episode_info?.epnum,
  }));

  return { to: '/download', state: { downloads } };
}

function Individual(props: {
  label: string;
  items?: MapType;
  season: number;
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
                <MLink {...download_all(parseInt(props.tmdb_id), torrents)}>
                  {name}
                </MLink>
              </h4>
              <ul>
                {torrents.map((t) => (
                  <li key={t.download}>
                    <DisplayTorrent
                      torrents={props.torrents}
                      torrent={t}
                      tmdb_id={props.tmdb_id}
                      season={props.season}
                      episode={t.episode_info?.epnum}
                    />
                  </li>
                ))}
              </ul>
            </div>
          ))}
      </ul>
      {props.items && !props.items.length && <p>No results found</p>}
    </div>
  );
}

export { DownloadAllComponent };
