import Breadcrumbs from '@mui/material/Breadcrumbs';
import Typography from '@mui/material/Typography';
import * as _ from 'lodash-es';
import ReactLoading from 'react-loading';
import { useParams } from 'react-router-dom';
import useSWR from 'swr';
import { MLink } from './MLink';
import * as qs from './qs';
import { RouteTitle } from './RouteTitle';
import type { components } from './schema';
import { useLocation } from './utils';

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

export function SeasonSelectComponent() {
  const { tmdb_id } = useParams<{ tmdb_id: string }>();
  const { data: tv } = useSWR<TV>(`tv/${tmdb_id}`);

  return (
    <RouteTitle title="Select Season">
      <Breadcrumbs aria-label="breadcrumb">
        <Shared />
        <Typography color="textPrimary" data-testid="title">
          {tv?.title}
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
    </RouteTitle>
  );
}
