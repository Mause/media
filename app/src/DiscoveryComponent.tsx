import useSWR from 'swr';
import { Grid } from '@mui/material';
import { faSearch } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

import type { paths } from './schema';
import { Loading } from './render';
import { MLink } from './MLink';
import { DisplayError } from './DisplayError';
import type { GetResponse } from './utils';
import { RouteTitle } from './RouteTitle';

export type DiscoverResponse = GetResponse<paths['/api/discover']>;
export type Configuration = GetResponse<paths['/api/tmdb/configuration']>;

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
    <RouteTitle title="Discover">
      <h3>Discovery</h3>
      <Loading loading={isValidating} />
      {error && <DisplayError error={error} />}
      <Grid container spacing={2}>
        {data?.results.map((result) => (
          <Grid key={result.id}>
            <h4>
              {result.title} ({getYear(result.release_date)})
              <MLink to={`/select/${result.id}/options`}>
                <FontAwesomeIcon icon={faSearch} />
              </MLink>
            </h4>
            {result.poster_path && <Poster poster_path={result.poster_path} />}
            <p>{result.overview}</p>
          </Grid>
        ))}
      </Grid>
    </RouteTitle>
  );
}

function Poster({ poster_path }: { poster_path: string }) {
  const { data, isValidating } = useSWR<Configuration>('tmdb/configuration');

  if (isValidating) {
    return undefined;
  }

  const base = data!.images.secure_base_url;
  const build = (size) => `${base}${size}${poster_path}`;

  const srcset = data!.images.poster_sizes
    .filter((size) => size !== 'original')
    .map((size) => [build(size), size]);

  const original = build('original');

  return (
    <img
      srcSet={srcset
        .map(([url, size]) => `${url} ${size.slice(1)}w`)
        .join(', ')}
      src={original}
    />
  );
}
