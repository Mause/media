import useSWR from 'swr';
import { Grid, styled } from '@mui/material';
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

const PREFIX = 'Poster';
const classes = {
  root: `${PREFIX}-root`,
};
const PosterElement = styled('div')(() => ({
  [`& .${classes.root}`]: {
    width: '100%',
  },
}));

function Poster({
  poster_path,
  build,
}: {
  poster_path: string;
  build: BuildFn;
}) {
  const { data } = useSWR<Configuration>('tmdb/configuration');

  const base = data?.images.secure_base_url;

  const srcset = data?.images.poster_sizes
    .filter((size) => size !== 'original')
    .map((size): [string, number] => [
      build(base, size, poster_path),
      Number.parseInt(size.slice(1)),
    ]);

  const original = build(base, 'original', poster_path);

  return (
    <PosterElement className={classes.root}>
      <picture>
        {srcset?.map(([url, size]) => (
          <source key={url} srcSet={url} width={size} height={size * 1.5} />
        ))}
        <img src={original} />
      </picture>
    </PosterElement>
  );
}
