import { useParams, Link, useLocation } from 'react-router-dom';
import _ from 'lodash';
import React from 'react';
import ReactLoading from 'react-loading';
import Typography from '@material-ui/core/Typography';
import Breadcrumbs from '@material-ui/core/Breadcrumbs';
import useSWR from 'swr';
import qs from 'qs';
import { MLink } from './utils';
import MateralLink from '@material-ui/core/Link';

export interface TV {
  number_of_seasons: number;
  title: string;
  seasons: { episode_count: number }[];
}

function Shared() {
  const { state } = useLocation<{ query: string }>();
  return (
    <Breadcrumbs>
      <MLink to="/">Home</MLink>
      {state ? (
        <MLink
          to={{
            pathname: '/search',
            search: qs.stringify({ query: state.query }),
          }}
        >
          Search Results
        </MLink>
      ) : (
        <MateralLink>Search Results</MateralLink>
      )}
    </Breadcrumbs>
  );
}

function SeasonSelectComponent() {
  const { tmdb_id } = useParams();
  const { data: tv } = useSWR<TV>(`tv/${tmdb_id}`);

  return <div>
    <Breadcrumbs aria-label="breadcrumb">
      <Shared />
      <Typography color="textPrimary" data-testid='title'>{tv && tv.title}</Typography>
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
  const { data: season } = useSWR<Season>(`tv/${tmdb_id}/season/${seasonNumber}`)
  const { data: tv } = useSWR<TV>(`tv/${tmdb_id}`);

  return <div>
    <Breadcrumbs aria-label="breadcrumb">
      <Shared />
      <MLink to={`/select/${tmdb_id}/season`}>{tv && tv.title}</MLink>
      <Typography color="textPrimary" data-testid='title'>Season {seasonNumber}</Typography>
    </Breadcrumbs>
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
