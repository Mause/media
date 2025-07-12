import useSWR from 'swr';
import {
  Grid,
  styled,
  IconButton,
  Card,
  CardHeader,
  CardContent,
  CardMedia,
} from '@mui/material';
import { faSearch } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useEffect, useRef, useState } from 'react';
import SearchIcon from '@mui/icons-material/Search';
import { Link } from 'react-router-dom';

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
            <Card variant="outlined">
              <CardHeader
                title={result.title}
                subheader={getYear(result.release_date)}
                action={
                  <IconButton
                    as={Link}
                    to={`/select/${result.id}/options`}
                    aria-label="search"
                  >
                    <SearchIcon />
                  </IconButton>
                }
              />
              {result.poster_path && (
                <CardMedia>
                  <Poster poster_path={result.poster_path} build={build} />
                </CardMedia>
              )}
              <CardContent>
                <p>{result.overview}</p>
              </CardContent>
            </Card>
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
  const [width, setWidth] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const { current } = ref;
    if (current) {
      setWidth(current.clientWidth);
    }
  }, [ref]);

  const base = data?.images?.secure_base_url;

  const srcset = data?.images.poster_sizes
    .filter((size) => size !== 'original')
    .map((size) => [build(base, size, poster_path), size]);

  const original = build(base, 'original', poster_path);

  return (
    <PosterElement ref={ref} className={classes.root}>
      <CardMedia
        component="img"
        style={{
          width,
          height: width * 1.5,
        }}
        srcSet={srcset
          ?.map(([url, size]) => `${url} ${size.slice(1)}${size[0]}`)
          .join(', ')}
        src={original}
      />
    </PosterElement>
  );
}
