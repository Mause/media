import useSWR from 'swr';
import { Grid } from '@mui/material';

import type { paths } from './schema';
import { Loading } from './render';
import { DisplayError } from './IndexComponent';

type DiscoverResponse =
  paths['/api/discover']['get']['responses']['200']['content']['application/json'];

export function DiscoveryComponent() {
  const { data, isValidating, error } = useSWR<DiscoverResponse, Error>(
    '/api/discover',
  );

  return (
    <div>
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
    </div>
  );
}
