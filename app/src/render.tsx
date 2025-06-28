import MenuItem from '@mui/material/MenuItem';
import { String } from 'typescript-string-operations';
// eslint-disable-next-line import-x/no-named-as-default
import Moment from 'moment';
import Collapsible from 'react-collapsible';
import { useNavigate } from 'react-router-dom';
import useSWR from 'swr';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faSearch,
  faSpinner,
  faCaretUp,
  faCaretDown,
  faCheckCircle,
} from '@fortawesome/free-solid-svg-icons';
import type { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import LinearProgress from '@mui/material/LinearProgress';
import * as _ from 'lodash-es';

import { getPrefix, MLink } from './utils';
import type { TV } from './SeasonSelectComponent';
import type {
  MovieResponse,
  SeriesResponse,
  Torrents,
  EpisodeResponse,
} from './streaming';
import ContextMenu from './ContextMenu';

export function Loading({
  loading,
  large,
}: {
  loading: boolean;
  large?: boolean;
}) {
  return loading ? (
    <FontAwesomeIcon
      spin={true}
      icon={faSpinner}
      size={large ? undefined : 'xs'}
    />
  ) : (
    <></>
  );
}

function OpenPlex({ download }: { download: { imdb_id: string } }) {
  return (
    <MenuItem
      component="a"
      href={`${getPrefix()}/redirect/plex/${download.imdb_id}`}
      target="_blank"
    >
      <span className="unselectable">Open in Plex</span>
    </MenuItem>
  );
}

export function Movies({
  movies,
  torrents,
  loading,
}: {
  movies: MovieResponse[];
  torrents?: Torrents;
  loading: boolean;
}) {
  const sortedMovies = _.groupBy(
    movies,
    (movie) => !!(torrents && getProgress(movie, torrents)?.percentDone === 1),
  );

  const head = (icon: IconDefinition) => (
    <h4>
      Finished downloads ({sortedMovies.true.length}){' '}
      <FontAwesomeIcon
        icon={icon}
        size="2x"
        style={{ cursor: 'pointer' }}
        transform={{ y: 2 }}
      />
    </h4>
  );

  return (
    <div className="colA">
      <h2>
        Movies <Loading loading={loading} />
      </h2>
      {sortedMovies?.true?.length ? (
        <Collapsible
          trigger={head(faCaretDown)}
          triggerElementProps={{
            id: `collapsible-trigger-complete-movies`,
          }}
          contentElementId="collapsible-content-complete-movies"
          triggerWhenOpen={head(faCaretUp)}
        >
          <ul>
            {(sortedMovies.true || []).map((movie) => (
              <li key={movie.id}>
                <span>{movie.download.title}</span>
              </li>
            ))}
          </ul>
        </Collapsible>
      ) : undefined}
      <ul>
        {(sortedMovies.false || []).map((movie) => (
          <li key={movie.id}>
            <span>{movie.download.title}</span>
            &nbsp;
            <ContextMenu>
              <OpenPlex download={movie.download} />
              <MenuItem
                component="a"
                href={`https://www.imdb.com/title/${movie.download.imdb_id}`}
                target="_blank"
              >
                Open in IMDB
              </MenuItem>
              {movie.download.added_by ? (
                <MenuItem>
                  Added by: {movie.download.added_by.username}
                </MenuItem>
              ) : null}
            </ContextMenu>
            &nbsp;
            <Progress torrents={torrents} item={movie} />
          </li>
        ))}
      </ul>
    </div>
  );
}

interface ShortDownload {
  transmission_id: string;
}

export function Progress({
  torrents,
  item,
}: {
  torrents?: Torrents;
  item: { download: ShortDownload };
}) {
  if (!torrents) return null;

  const prog = getProgress(item, torrents);
  if (!prog) return null;

  const { eta, percentDone } = prog;
  if (percentDone === 1) {
    return <FontAwesomeIcon icon={faCheckCircle} />;
  } else {
    const etaDescr =
      eta > 0 ? Moment().add(eta, 'seconds').fromNow(true) : 'Unknown time';
    const title = String.format(
      '{0:00}% ({1} remaining)',
      percentDone * 100,
      etaDescr,
    );
    return (
      <LinearProgress
        variant="determinate"
        value={percentDone * 100}
        title={title}
      />
    );
  }
}

export function getMarker(episode: {
  season?: number;
  episode?: number | null;
}) {
  return String.format('S{0:00}E{1:00}', episode.season, episode.episode);
}

function getProgress(
  item: { download: ShortDownload },
  torrents: Torrents,
): { eta: number; percentDone: number } | null {
  let eta,
    percentDone,
    tid = item.download.transmission_id;
  if (tid.includes('.')) {
    tid = tid.split('.')[0];
    const marker = getMarker(item as EpisodeResponse);
    const torrent = torrents[tid];
    if (!torrent) return null;
    eta = torrent.eta;
    const tf = torrent.files.find((file) => file.name.includes(marker));
    if (tf) {
      percentDone = tf.bytesCompleted / tf.length;
    } else {
      percentDone = torrent.percentDone;
    }
  } else {
    if (!(tid in torrents)) return null;
    ({ eta, percentDone } = torrents[tid]);
  }
  return { eta, percentDone };
}

export function TVShows({
  series,
  torrents,
  loading,
}: {
  series: SeriesResponse[];
  torrents?: Torrents;
  loading: boolean;
}) {
  return (
    <div>
      <div className="colB">
        <h2>
          TV Shows <Loading loading={loading} />
        </h2>
        {series.map((serie) => (
          <Series key={serie.tmdb_id} serie={serie} torrents={torrents} />
        ))}
      </div>
    </div>
  );
}

function Series({
  serie,
  torrents,
}: {
  serie: SeriesResponse;
  torrents?: Torrents;
}) {
  const { data } = useSWR<TV>(`tv/${serie.tmdb_id}`);
  const navigate = useNavigate();
  return (
    <div>
      <h3>
        {serie.title}
        &nbsp;
        <ContextMenu>
          {serie.imdb_id && (
            <MenuItem
              component="a"
              href={`https://www.imdb.com/title/${serie.imdb_id}`}
              target="_blank"
            >
              Open in IMDB
            </MenuItem>
          )}
          <OpenPlex download={serie} />
          <MenuItem
            onClick={() => void navigate(`/select/${serie.tmdb_id}/season`)}
          >
            Search
          </MenuItem>
        </ContextMenu>
      </h3>
      {_.sortBy(Object.entries(serie.seasons), ([key]) => parseInt(key)).map(
        ([i, season]) => (
          <Season
            key={i}
            i={i}
            season={season}
            tmdb_id={serie.tmdb_id}
            torrents={torrents}
            collapse={shouldCollapse(i, data, season)}
          />
        ),
      )}
    </div>
  );
}

function Season({
  i,
  collapse,
  season,
  tmdb_id,
  torrents,
}: {
  collapse: boolean;
  i: string;
  torrents?: Torrents;
  season: EpisodeResponse[];
  tmdb_id: number;
}) {
  const head = (icon: IconDefinition) => (
    <h4>
      Season {i} {collapse && '(Complete) '}
      &nbsp;
      <MLink to={`/select/${tmdb_id}/season/${i}`}>
        <FontAwesomeIcon icon={faSearch} />
      </MLink>
      &nbsp;
      <FontAwesomeIcon
        icon={icon}
        size="2x"
        style={{ cursor: 'pointer' }}
        transform={{ y: 2 }}
      />
    </h4>
  );
  return (
    <Collapsible
      trigger={head(faCaretDown)}
      triggerElementProps={{
        id: `collapsible-trigger-tv-${tmdb_id}-season-${i}`,
      }}
      contentElementId={`collapsible-content-tv-${tmdb_id}-season-${i}`}
      triggerWhenOpen={head(faCaretUp)}
      open={!collapse}
    >
      <ol>
        {season.map((episode) => (
          <li key={episode.id} value={episode.episode!}>
            <span>{episode.download.title}</span>
            &nbsp;
            <Progress torrents={torrents} item={episode} />
          </li>
        ))}
        <NextEpisodeAirs
          tmdb_id={tmdb_id}
          season={i}
          season_episodes={season}
        />
      </ol>
    </Collapsible>
  );
}

export function NextEpisodeAirs(props: {
  tmdb_id: number;
  season: string;
  season_episodes: { episode: number | null }[];
}) {
  const { data } = useSWR<{
    episodes: { name: string; air_date: string; episode_number: number }[];
  }>(`tv/${props.tmdb_id}/season/${props.season}`);

  if (!data) {
    return <></>;
  }

  const lastEpisode = _.last(props.season_episodes)!.episode!;

  const nextEpisode = data.episodes.find(
    (episode) => episode.episode_number === lastEpisode + 1,
  );
  if (!nextEpisode) {
    return <></>;
  }

  let message = getMessage(nextEpisode.air_date);

  const ep_num = `Episode ${nextEpisode.episode_number}`;
  if (ep_num === nextEpisode.name) {
    // unoriginal episode names
    message = `${ep_num} ${message}`;
  } else {
    message = ep_num + ` "${nextEpisode.name}" ` + message;
  }

  return (
    <small>
      {message}&nbsp;
      <MLink
        to={`/select/${props.tmdb_id}/season/${props.season}/episode/${nextEpisode.episode_number}/options`}
      >
        <FontAwesomeIcon icon={faSearch} />
      </MLink>
    </small>
  );
}

export function getMessage(air_date: string, today_s?: string): string {
  const today = Moment(today_s).startOf('day');
  const tomorrow = today.add(1, 'day');
  const yesterday = today.subtract(1, 'day');
  const dt = Moment(air_date);
  const dts = dt.format('DD/MM/YYYY');

  let message;
  if (today.isSame(dt)) {
    message = 'airs today';
  } else if (dt.isSame(yesterday)) {
    message = 'aired yesterday';
  } else if (dt.isSame(tomorrow)) {
    message = 'airs tomorrow';
  } else if (dt.isAfter(today)) {
    message = 'airs on ' + dts;
  } else {
    message = 'aired on ' + dts;
  }
  return message;
}

export function shouldCollapse(
  i: string,
  data: TV | undefined,
  episodes: EpisodeResponse[],
): boolean {
  let collapse = false;
  if (data) {
    const i_i = +i;
    const seasonMeta = data.seasons.find((s) => s.season_number === i_i);
    if (seasonMeta) {
      const hasNext = true; // !!data.seasons[i_i + 1];

      const episodeNumbers = _.range(1, seasonMeta.episode_count + 1);
      const hasNumbers = _.map(episodes, 'episode');
      const hasAllEpisodes =
        _.difference(episodeNumbers, hasNumbers).length === 0;
      collapse = hasNext && hasAllEpisodes;
    }
  }
  return collapse;
}
