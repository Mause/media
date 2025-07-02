import useSWR from 'swr';
import { Grid } from '@mui/material';

import type { paths } from './schema';
import { Loading } from './render';
import { DisplayError } from './DisplayError';
import type { GetResponse } from './utils';
import { RouteTitle } from './RouteTitle';

type DiscoverResponse = GetResponse<paths['/api/discover']>;

export function DiscoveryComponent() {
  const { data, isValidating, error } = useSWR<DiscoverResponse, Error>(
    'discover',
  );

  return (
    <RouteTitle title="Discover">
      <h3>DiscoveryComponent</h3>
      <Loading loading={isValidating} />
      {error && <DisplayError error={error} />}
      <Grid container spacing={2}>
        {data?.results.map((result) => (
          <Grid>
            <h4>{result.title}</h4>
            <p>{result.overview}</p>
          </Grid>
        ))}
      </Grid>
    </RouteTitle>
  );
}
