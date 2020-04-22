import _ from 'lodash';
import React from 'react';
import {
  MovieResponse,
  SeriesResponse,
  Torrents,
  EpisodeResponse,
} from './streaming';
import { String } from 'typescript-string-operations';
import Moment from 'moment';
import { ContextMenu, ContextMenuTrigger, MenuItem } from 'react-contextmenu';
import Collapsible from 'react-collapsible';
import { useHistory } from 'react-router-dom';
import { TV } from './SeasonSelectComponent';
import useSWR from 'swr';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faSearch,
  faSpinner,
  faCaretUp,
  faCaretDown,
  faList,
  faCheckCircle,
} from '@fortawesome/free-solid-svg-icons';
import { MLink } from './utils';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';

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

function openPlex(item: { download: { imdb_id: string } }) {
  window.open(`/redirect/plex/${item.download.imdb_id}`);
}

export function contextMenuTrigger(id: string) {
  // workaround for type issue
  const props = { mouseButton: 0 };
  return (
    <ContextMenuTrigger
      {...props}
      id={id}
      attributes={{
        style: { cursor: 'pointer', display: 'inline' },
      }}
    >
      <FontAwesomeIcon icon={faList} />
    </ContextMenuTrigger>
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
    movie => !!(torrents && getProgress(movie, torrents)?.percentDone === 1),
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
          triggerWhenOpen={head(faCaretUp)}
        >
          <ul>
            {(sortedMovies.true || []).map(movie => (
              <li key={movie.id}>
                <span>{movie.download.title}</span>
              </li>
            ))}
          </ul>
        </Collapsible>
      ) : (
        undefined
      )}
      <ul>
        {(sortedMovies.false || []).map(movie => (
          <li key={movie.id}>
            <span>{movie.download.title}</span>
            &nbsp;
            {contextMenuTrigger(`movie_${movie.id}`)}
            <ContextMenu id={`movie_${movie.id}`}>
              <MenuItem onClick={() => openPlex(movie)}>
                <span className="unselectable">Play in Plex</span>
              </MenuItem>
              <MenuItem
                onClick={() =>
                  window.open(
                    `https://www.imdb.com/title/${movie.download.imdb_id}`,
                  )
                }
              >
                Open in IMDB
              </MenuItem>
              {movie.download.added_by ? (
                <MenuItem>
                  Added by: {movie.download.added_by.first_name}
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
      eta > 0
        ? Moment()
            .add(eta, 'seconds')
            .fromNow(true)
        : 'Unknown time';
    const title = String.Format(
      '{0:00}% ({1} remaining)',
      percentDone * 100,
      etaDescr,
    );
    return <progress value={percentDone} title={title} />;
  }
}

export function getMarker(episode: { season: any; episode: any }) {
  return String.Format('S{0:00}E{1:00}', episode.season, episode.episode);
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
    const tf = torrent.files.find(file => file.name.includes(marker));
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
        {series.map(serie => (
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
  const history = useHistory();
  return (
    <div>
      <h3>
        {serie.title}
        &nbsp;
        {contextMenuTrigger(`tv_${serie.imdb_id}`)}
        <ContextMenu id={`tv_${serie.imdb_id}`}>
          {serie.imdb_id && (
            <MenuItem
              onClick={() =>
                window.open(`https://www.imdb.com/title/${serie.imdb_id}`)
              }
            >
              Open in IMDB
            </MenuItem>
          )}
          <MenuItem
            onClick={() => history.push(`/select/${serie.tmdb_id}/season`)}
          >
            Search
          </MenuItem>
        </ContextMenu>
      </h3>
      {_.sortBy(_.toPairs(serie.seasons), ([key]) => parseInt(key)).map(
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
  tmdb_id: string;
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
      triggerWhenOpen={head(faCaretUp)}
      open={!collapse}
    >
      <ol>
        {season.map(episode => (
          <li key={episode.episode} value={episode.episode}>
            <span>{episode.download.title}</span>
            &nbsp;
            <Progress torrents={torrents} item={episode} />
          </li>
        ))}
        <NextEpisodeAirs tmdb_id={tmdb_id} season={i} />
      </ol>
    </Collapsible>
  );
}

function NextEpisodeAirs(props: { tmdb_id: string; season: string }) {
  const { data } = useSWR<{ episodes: { name: string; air_date: string; episode_number: number }[] }>(
    `tv/${props.tmdb_id}/season/${props.season}`,
  );

  if (!data) {
    return <></>;
  }

  const now = Moment();
  const nextEpisode = data.episodes.find(episode =>
    Moment(episode.air_date).isSameOrAfter(now, 'day'),
  );
  if (!nextEpisode) {
    return <></>;
  }

  const dt = Moment(nextEpisode.air_date).format('DD/MM/YYYY');
  return (
    <small>
      Episode {nextEpisode.episode_number} "{nextEpisode.name}" airs on {dt}
    </small>
  );
}

export function shouldCollapse(
  i: string,
  data: TV | undefined,
  episodes: EpisodeResponse[],
): boolean {
  let collapse = false;
  if (data) {
    const i_i = +i;
    const seasonMeta = data.seasons.find(s => s.season_number === i_i);
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
