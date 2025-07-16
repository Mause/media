import Breadcrumbs from '@mui/material/Breadcrumbs';
import Typography from '@mui/material/Typography';
import { useParams } from 'react-router-dom';
import useSWR from 'swr';

import { Loading } from '../render';
import { MLink } from '../MLink';
import { RouteTitle } from '../RouteTitle';

import type { Season, TV } from './SeasonSelectComponent';
import { Shared } from './SeasonSelectComponent';

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

export function EpisodeSelectComponent() {
  const { tmdb_id, season: seasonNumber } = useParams<{
    tmdb_id: string;
    season: string;
  }>();
  const { data: season } = useSWR<Season>(
    `tv/${tmdb_id}/season/${seasonNumber}`,
  );

  return (
    <RouteTitle title="Select Episode">
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
        <Loading loading />
      )}
      <MLink to={`/select/${tmdb_id}/season/${seasonNumber}/download_all`}>
        Download season
      </MLink>
      <br />
    </RouteTitle>
  );
}
