import _ from 'lodash';
import React from 'react';
import { Download, MovieResponse, SeriesResponse, Torrents, EpisodeResponse } from './streaming';
import { String } from 'typescript-string-operations';
import Moment from "moment";
import { ContextMenu, ContextMenuTrigger, MenuItem } from "react-contextmenu";
import { load } from './utils';
import { Link } from 'react-router-dom';

function Loading({ loading }: { loading: boolean }) {
  return loading ? <i className="fas fa-spinner fa-spin fa-xs" /> : <></>
}

function plex(plexId: string, serverId: string): string {
  return `https://app.plex.tv/desktop#!/server/${serverId}/details?` + new URLSearchParams({ 'key': '/library/metadata/' + plexId });
}

function openPlex(movie: { download: { imdb_id: string } }) {
  load<{ id: string, server_id: string }>(`plex/${movie.download.imdb_id}`).then(
    ({ id, server_id }) => window.open(plex(id, server_id))
  );
}

function contextMenuTrigger(id: string) {
  // @ts-ignore
  return <ContextMenuTrigger mouseButton={0}
    id={id}
    renderTag='i'
    attributes={{
      className: 'fas fa-list',
      style: { cursor: 'pointer' },
    }}
    children={''}
  />
}

export function Movies({ movies, torrents, loading }: { movies: MovieResponse[], torrents?: Torrents, loading: boolean }) {
  return <div className="colA">
    <h2>Movies <Loading loading={loading} /></h2>
    <ul>
      {movies.map(movie =>
        <li key={movie.id}>
          <span>{movie.download.title}</span>
          &nbsp;
          {contextMenuTrigger(`movie_${movie.id}`)}
          <ContextMenu id={`movie_${movie.id}`}>
            <MenuItem onClick={() => openPlex(movie)}><span className="unselectable">Play in Plex</span></MenuItem>
            <MenuItem onClick={() => window.open(`https://www.imdb.com/title/${movie.download.imdb_id}`)}>Open in IMDB</MenuItem>
          </ContextMenu>
          &nbsp;
          <Progress torrents={torrents} item={movie} />
        </li>
      )}
    </ul>
  </div>
}

function Progress({ torrents, item }: { torrents?: Torrents, item: { download: Download } }) {
  if (!torrents) return null;

  let { eta, percentDone } = getProgress(item.download.transmission_id, item, torrents);
  if (percentDone == 1) {
    return <i className="fas fa-check-circle"></i>
  } else {
    let etaDescr = eta > 0 ? Moment().add(eta, 'seconds').fromNow(true) : 'Unknown time'
    const title = String.Format("{0:00}% ({1} remaining)", percentDone * 100, etaDescr);
    return <progress value={percentDone} title={title}></progress>
  }
}

function getProgress(tid: string, item: { download: Download; }, torrents: Torrents): { eta: number, percentDone: number } {
  let eta, percentDone;
  if (tid.includes('.')) {
    tid = tid.split('.')[0];
    const episode = item as EpisodeResponse;
    const marker = String.Format('S{0:00}E{0:00}', episode.season, episode.episode);
    const torrent = torrents[tid];
    eta = torrent.eta;
    const tf = torrent.files.find(file => file.name.includes(marker));
    if (tf) {
      percentDone = tf.bytesCompleted / tf.length;
    } else {
      percentDone = torrent.percentDone;
    }
  } else {
    ({ eta, percentDone } = torrents[tid]);
  }
  return { eta, percentDone };
}

export function TVShows({ series, torrents, loading }: {
  series: SeriesResponse[];
  torrents?: Torrents;
  loading: boolean;
}) {
  return <div>
    <div className="colB">
      <h2>TV Shows <Loading loading={loading} /></h2>
      {series.map(serie => <div key={serie.imdb_id}>
        <h3>
          {serie.title}
          &nbsp;
          <Link to={`/select/${serie.tmdb_id}/season`}>
            <i className="fas fa-search" />
          </Link>
        </h3>
        {_.sortBy(Object.keys(serie.seasons), parseInt).map(i => {
          const season = serie.seasons[i];
          return <div key={i}>
            <h4>
              Season {i}
              &nbsp;
              <Link to={`/select/${serie.tmdb_id}/season/${i}`}>
                <i className="fas fa-search" />
              </Link>
            </h4>
            <ol>
              {season.map(episode => <li key={episode.episode} value={episode.episode}>
                <span>{episode.download.title}</span>
                &nbsp;
                <Progress torrents={torrents} item={episode} />
              </li>)}
            </ol>
          </div>;
        })}
      </div>)}
    </div>
  </div>;
}
