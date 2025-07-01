import useSWR from 'swr';
import { Grid } from '@mui/material';
import { faSearch } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

import type { paths } from './schema';
import { Loading } from './render';
import { MLink } from './MLink';
import { DisplayError } from './IndexComponent';
import type { GetResponse } from './utils';

type DiscoverResponse = GetResponse<paths['/api/discover']>;

function getYear(release_date: string | null | undefined): string | number {
  if (release_date) {
    return new Date(release_date).getFullYear();
  } else {
    return 'Unknown';
  }
}

export function DiscoveryComponent() {
  const { data, isValidating, error } = useSWR<DiscoverResponse, Error>(
    'discover',
  );

  return (
    <div>
      <h3>Discovery</h3>
      <Loading loading={isValidating} />
      {error && <DisplayError error={error} />}
      <Grid container spacing={2}>
        {data?.results.map((result) => (
          <Grid>
            <h4>
              {result.title} ({getYear(result.release_date)})
              <MLink to={`/select/${result.id}/options`}>
                <FontAwesomeIcon icon={faSearch} />
              </MLink>
            </h4>
            <p>{result.overview}</p>
          </Grid>
        ))}
      </Grid>
    </div>
  );
}
