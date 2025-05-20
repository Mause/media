import { useParams } from 'react-router-dom';
import _ from 'lodash';
import React from 'react';
import ReactLoading from 'react-loading';
import Typography from '@mui/material/Typography';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import useSWR from 'swr';
import qs from 'qs';

import { components } from './schema';
import { MLink, useLocation } from './utils';

export type Season = components['schemas']['TvSeasonResponse'];
export type EpisodeResponse = components['schemas']['Episode'];
export type TV = components['schemas']['TvResponse'];

export function Shared() {
  const { state } = useLocation<{ query: string }>();
  return (
    <Breadcrumbs>
      <MLink color="inherit" to="/">
        Home
      </MLink>
      {state ? (
        <MLink
          color="inherit"
          to={{
            pathname: '/search',
            search: qs.stringify({ query: state.query }),
          }}
        >
          Search Results
        </MLink>
      ) : (
        <Typography>Search Results</Typography>
      )}
    </Breadcrumbs>
  );
}

function SeasonSelectComponent() {
  const { tmdb_id } = useParams<{ tmdb_id: string }>();
  const { data: tv } = useSWR<TV>(`tv/${tmdb_id}`);

  return (
    <div>
      <Breadcrumbs aria-label="breadcrumb">
        <Shared />
        <Typography color="textPrimary" data-testid="title">
          {tv && tv.title}
        </Typography>
      </Breadcrumbs>
      {!tv ? (
        <ReactLoading type="balls" color="#000000" />
      ) : (
        <ul>
          {_.range(1, tv.number_of_seasons + 1).map((i) => (
            <li key={i}>
              <MLink to={`/select/${tmdb_id}/season/${i}`}>Season {i}</MLink>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function EpisodeSelectBreadcrumbs(props: {
  tmdb_id: string;
  season: number;
}) {
  const { data: tv } = useSWR<TV>(`tv/${props.tmdb_id}`);

  return (
    <Breadcrumbs aria-label="breadcrumb">
      <Shared />
      <MLink color="inherit" to={`/select/${props.tmdb_id}/season`}>
        {tv ? tv.title : ''}
      </MLink>
      <Typography color="textPrimary" data-testid="title">
        Season {props.season}
      </Typography>
    </Breadcrumbs>
  );
}

function EpisodeSelectComponent() {
  const { tmdb_id, season: seasonNumber } = useParams<{
    tmdb_id: string;
    season: string;
  }>();
  const { data: season } = useSWR<Season>(
    `tv/${tmdb_id}/season/${seasonNumber}`,
  );

  return (
    <div>
      <EpisodeSelectBreadcrumbs
        tmdb_id={tmdb_id!}
        season={parseInt(seasonNumber!)}
      />
      {season ? (
        <ol>
          {season.episodes.map((episode) => (
            <li key={episode.id} value={episode.episode_number}>
              <MLink
                to={`/select/${tmdb_id}/season/${seasonNumber}/episode/${episode.episode_number}/options`}
              >
                {episode.name}
              </MLink>
            </li>
          ))}
        </ol>
      ) : (
        <ReactLoading type="balls" color="#000" />
      )}
      <MLink to={`/select/${tmdb_id}/season/${seasonNumber}/download_all`}>
        Download season
      </MLink>
      <br />
    </div>
  );
}

export { SeasonSelectComponent, EpisodeSelectComponent };
