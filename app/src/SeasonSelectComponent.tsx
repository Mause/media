import { useParams, Link } from 'react-router-dom';
import { useLoad } from './utils';
import _ from 'lodash';
import React from 'react';
import ReactLoading from 'react-loading';
import Typography from '@material-ui/core/Typography';
import Breadcrumbs from '@material-ui/core/Breadcrumbs';
import MLink from '@material-ui/core/Link';

export interface TV {
  number_of_seasons: number;
  title: string;
  seasons: { episode_count: number }[];
}

function SeasonSelectComponent() {
  const { tmdb_id } = useParams();
  const tv = useLoad<TV>(`tv/${tmdb_id}`);

  return <div>
    <h3 data-testid='title'>{tv && tv.title}</h3>
    <Breadcrumbs aria-label="breadcrumb">
      <MLink color="inherit">
        <Link to='/'>Home</Link>
      </MLink>
      <MLink color="inherit">
        Search Results
      </MLink>
      <Typography color="textPrimary">Season Select</Typography>
    </Breadcrumbs>
    {!tv ?
      <ReactLoading type='balls' color='#000000' /> :
      <ul>
        {_.range(1, tv.number_of_seasons + 1).map(i =>
          <li key={i}>
            <Link to={`/select/${tmdb_id}/season/${i}`}>
              Season {i}
            </Link>
          </li>
        )}
      </ul>
    }
  </div>;
}

interface Episode {
  episode_number: number;
  id: string;
  name: string;
}
export interface Season {
  episodes: Episode[];
}
function EpisodeSelectComponent() {
  const { tmdb_id, season: seasonNumber } = useParams();
  const season = useLoad<Season>(`tv/${tmdb_id}/season/${seasonNumber}`)

  return <div>
    <h3 data-testid='title'>Season {seasonNumber}</h3>
    <Link to={`/select/${tmdb_id}/season`}><small>Back to seasons</small></Link>
    {season ? <ol>
      {season.episodes.map(episode =>
        <li key={episode.id} value={episode.episode_number}>
          <Link to={`/select/${tmdb_id}/season/${seasonNumber}/episode/${episode.episode_number}/options`}>
            {episode.name}
          </Link>
        </li>
      )}
    </ol> : <ReactLoading type='balls' color='#000' />}
    <a href={`/select/${tmdb_id}/season/${seasonNumber}/download_all`}>Download season</a>
    <br />
  </div>;
}

export { SeasonSelectComponent, EpisodeSelectComponent };
