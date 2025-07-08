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

export type DiscoverResponse = Pick<
  GetResponse<paths['/api/discover']>,
  'results'
>;
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
    <PureDiscoveryComponent
      data={data}
      isValidating={isValidating}
      error={error}
      build={build}
    />
  );
}

const build = (base: string | undefined, size: string, poster_path: string) =>
  `${base}${size}${poster_path}`;
type BuildFn = typeof build;

export function PureDiscoveryComponent({
  data,
  isValidating,
  error,
  build,
}: {
  isValidating: boolean;
  error: Error | undefined;
  data: DiscoverResponse | undefined;
  build: BuildFn;
}) {
  return (
    <RouteTitle title="Discover">
      <h3>Discovery</h3>
      <Loading loading={isValidating} />
      {error && <DisplayError error={error} />}
      <Grid container spacing={2}>
        {data?.results.map((result) => (
          <Grid key={result.id} size={{ xs: 12, sm: 6, lg: 2 }}>
            <h4>
              {result.title} ({getYear(result.release_date)}){' '}
              <MLink to={`/select/${result.id}/options`}>
                <FontAwesomeIcon icon={faSearch} />
              </MLink>
            </h4>
            {result.poster_path && (
              <Poster poster_path={result.poster_path} build={build} />
            )}
            <p>{result.overview}</p>
          </Grid>
        ))}
      </Grid>
    </RouteTitle>
  );
}

function Poster({
  poster_path,
  build,
}: {
  poster_path: string;
  build: BuildFn;
}) {
  const { data, isValidating } = useSWR<Configuration>('tmdb/configuration');

  if (isValidating) {
    return undefined;
  }

  const base = data!.images.secure_base_url;

  const srcset = data!.images.poster_sizes
    .filter((size) => size !== 'original')
    .map((size) => [build(base, size, poster_path), size]);

  const original = build(base, 'original', poster_path);

  return (
    <img
      style={{ width: '100%' }}
      srcSet={srcset
        .map(([url, size]) => `${url} ${size.slice(1)}${size[0]}`)
        .join(', ')}
      src={original}
    />
  );
}
