import { useEffect, useState } from 'react';
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
  faCaretUp,
  faCaretDown,
  faCheckCircle,
} from '@fortawesome/free-solid-svg-icons';
import type { IconDefinition } from '@fortawesome/fontawesome-svg-core';
import LinearProgress from '@mui/material/LinearProgress';
import * as _ from 'lodash-es';
import { useAuth0 } from '@auth0/auth0-react';
import usePromise from 'react-promise-suspense';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContentText from '@mui/material/DialogContentText';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';

import { useMessage, readyStateToString, nextId } from './components/websocket';
import { getMarker, getMessage, getToken, shouldCollapse } from './utils';
import type { TV } from './select/SeasonSelectComponent';
import type {
  MovieResponse,
  SeriesResponse,
  Torrents,
  EpisodeResponse,
} from './ParentComponent';
import { ContextMenu, Loading, MLink } from './components';
import type { components } from './schema';

function OpenIMDB({ download }: { download: { imdb_id: string } }) {
  return (
    <MenuItem
      component="a"
      href={`https://www.imdb.com/title/${download.imdb_id}`}
      target="_blank"
    >
      Open in IMDB
    </MenuItem>
  );
}

type PlexRootResponse = components['schemas']['PlexRootResponse'];
type PlexRequest = components['schemas']['PlexRequest'];

function OpenNewWindow({ link, label }: { link: string; label: string }) {
  useEffect(() => {
    window.open(link, '_blank', 'noopener,noreferrrer');
  }, [link]);

  return (
    <div>
      Opening <a href={link}>{label}</a>
    </div>
  );
}

function OpenPlex({
  download,
  type,
}: {
  download: { tmdb_id: number };
  type: 'movie' | 'tv';
}) {
  const auth = useAuth0();
  const [open, setOpen] = useState(false);
  const token = 'Bearer ' + usePromise(() => getToken(auth), []);
  const { message, trigger, readyState, state } = useMessage<
    PlexRequest,
    PlexRootResponse
  >({
    method: 'plex',
    jsonrpc: '2.0',
    id: nextId(),
    authorization: token,
    params: {
      tmdb_id: download.tmdb_id,
      media_type: type,
    },
  });

  if (message) {
    const first = _.values(message.result).find((v) => v)!;
    return <OpenNewWindow link={first.link} label={first.item.title} />;
  }

  return (
    <>
      <Dialog open={open}>
        <DialogTitle>Search plex for media...</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {readyStateToString(readyState)}<br />
            {state}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
      <MenuItem
        onClick={() => {
          setOpen(true);
          trigger();
        }}
      >
        <span className="unselectable">Open in Plex</span>
      </MenuItem>
    </>
  );
}

function RenderMovie({ movie }: { movie: MovieResponse }) {
  return (
    <>
      <span>{movie.download.title}</span>
      &nbsp;
      <ContextMenu>
        <OpenPlex download={movie.download} type="movie" />
        <OpenIMDB download={movie.download} />
        {movie.download.added_by ? (
          <MenuItem>Added by: {movie.download.added_by.username}</MenuItem>
        ) : null}
      </ContextMenu>
    </>
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
    (movie) =>
      torrents !== undefined && getProgress(movie, torrents)?.percentDone === 1,
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
                <RenderMovie movie={movie} />
              </li>
            ))}
          </ul>
        </Collapsible>
      ) : undefined}
      <ul>
        {(sortedMovies.false || []).map((movie) => (
          <li key={movie.id}>
            <RenderMovie movie={movie} />
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
          {serie.imdb_id && <OpenIMDB download={serie} />}
          <OpenPlex download={serie} type="tv" />
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
