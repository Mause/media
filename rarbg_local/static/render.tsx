import _ from 'lodash';
import React from 'react';
import { Download, MovieResponse, SeriesResponse, Torrents } from './streaming';
import { String } from 'typescript-string-operations';
import Moment from "moment";

export function Movies({ movies, torrents }: { movies: MovieResponse[], torrents: Torrents }) {
    return <div className="colA">
        <h2>Movies</h2>
        <ul>
            {movies.map(movie =>
                <li key={movie.id}>
                    <span>{movie.download.title}</span>
                    <small>
                        <a target="_blank" href="https://www.imdb.com/title/{{movie.download.imdb_id}}">
                            <i className="fas fa-share"></i>
                        </a>
                    </small>
                    <Progress torrents={torrents} item={movie} />
                </li>
            )}
        </ul>
    </div>
}

function Progress({ torrents, item }: { torrents: Torrents, item: { download: Download } }) {
    let tid = item.download.transmission_id
    let { percentDone, eta } = torrents[tid] || { percentDone: 1, eta: 0 };

    if (percentDone == 1) {
        return <i className="fas fa-check-circle"></i>
    } else {
        let etaDescr = eta > 0 ? Moment().add(eta, 'seconds').fromNow(true) : 'Unknown time'
        const title = String.Format("{0:00}% ({1} remaining)", percentDone * 100, etaDescr);
        return <progress value={percentDone} title={title}></progress>
    }
}

export function TVShows({ series, torrents }: {
    series: SeriesResponse[];
    torrents: Torrents;
}) {
    return <div>
        <div className="colB">
            <h2>TV Shows</h2>
            {series.map(serie => <div key={serie.imdb_id}>
                <h3>{serie.title}</h3>
                {_.sortBy(Object.keys(serie.seasons), parseInt).map(i => {
                    const season = serie.seasons[i];
                    return <div key={i}>
                        <h4>Season {i}</h4>
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
