import _ from 'lodash';
import React from 'react';
import { Download, MovieResponse, SeriesResponse, Torrents } from './streaming';

export function Movies({ movies, torrents }: { movies: MovieResponse[], torrents: Torrents }) {
    return <div>{movies.length}</div>
}

function getPercent(torrents: Torrents, hasDownload: { download: Download }): number {
    const torrent = torrents[hasDownload.download.transmission_id];
    return torrent ? torrent.percentDone : 1;
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
                <progress value={getPercent(torrents, episode)} />
                            </li>)}
                        </ol>
                    </div>;
                })}
            </div>)}
        </div>
    </div>;
}
