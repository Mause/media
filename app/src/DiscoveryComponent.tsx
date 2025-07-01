import useSWR from 'swr';
import { Grid } from '@mui/material';

import type { paths } from './schema';
import { Loading } from './render';
import { MLink } from './MLink';
import { DisplayError } from './IndexComponent';
import { faSearch } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

type DiscoverResponse =
  paths['/api/discover']['get']['responses']['200']['content']['application/json'];

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
              {result.title}
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
