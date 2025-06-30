import type { LoaderFunction } from 'react-router-dom';
import { useLoaderData } from 'react-router-dom';
import { Grid } from '@mui/material';

import type { paths } from './schema';

type DiscoverResponse =
  paths['/api/discover']['get']['responses']['200']['content']['application/json'];

export const loader = (async () => {
  // TODO: auth
  const res = await fetch('/api/discover');

  const data = (await res.json()) as unknown as DiscoverResponse;

  return { data };
}) satisfies LoaderFunction;

export function DiscoveryComponent() {
  const { data } = useLoaderData<typeof loader>();

  return (
    <div>
      <h3>Discovery Component</h3>
      <p>This is a placeholder for the Discovery component.</p>
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
