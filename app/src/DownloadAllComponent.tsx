import { useParams } from 'react-router-dom';
import useSWR from 'swr';
import { DisplayError } from './DisplayError';
import { DisplayTorrent } from './DisplayTorrent';
import type { DownloadCall } from './DownloadComponent';
import { EpisodeSelectBreadcrumbs } from './EpisodeSelectComponent';
import type { ManualAddComponentState } from './ManualAddComponent';
import { MLink } from './MLink';
import type { ITorrent } from './OptionsComponent';
import { RouteTitle } from './RouteTitle';
import { Loading } from './render';
import type { paths } from './schema';
import type { Torrents } from './streaming';
import type { GetResponse } from './utils';

type DownloadAllResponse = GetResponse<
  paths['/api/select/{tmdb_id}/season/{season}/download_all']
>;
type MapType = DownloadAllResponse['complete'];

function DownloadAllComponent() {
  const { tmdb_id, season: season_s } = useParams<{
    tmdb_id: string;
    season: string;
  }>();
  const season = parseInt(season_s!);

  const { data: torrents } = useSWR<Torrents>('torrents');
  const { data, isValidating, error } = useSWR<DownloadAllResponse, Error>(
    `select/${tmdb_id}/season/${season}/download_all`,
  );

  return (
    <RouteTitle title="Download Season">
      {error && <DisplayError error={error} />}
      <EpisodeSelectBreadcrumbs tmdb_id={tmdb_id!} season={season} />
      <Loading loading={isValidating} />
      <div>
        <h3>Packs</h3>
        <ul>
          {data?.packs?.map((t) => (
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
        items={data?.complete}
        season={season}
        tmdb_id={tmdb_id!}
        torrents={torrents}
      />
      <Individual
        label="Incomplete Sets"
        items={data?.incomplete}
        season={season}
        tmdb_id={tmdb_id!}
        torrents={torrents}
      />

      <ul>
        <li>
          <MLink
            to="/manual"
            state={
              {
                tmdb_id: tmdb_id!,
                season: season_s!,
              } satisfies ManualAddComponentState
            }
          >
            Add manually
          </MLink>
        </li>
      </ul>
    </RouteTitle>
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
        {props.items?.map(([name, torrents]) => (
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
