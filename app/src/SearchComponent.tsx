import { useLocation } from 'react-router-dom';
import useSWR from 'swr';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTicketAlt, faTv } from '@fortawesome/free-solid-svg-icons';

import {
  DisplayError,
  MLink,
  SearchBox,
  RouteTitle,
  Loading,
} from './components';
import type { components, paths } from './schema';
import type { GetResponse } from './utils';

export type SearchResponse = GetResponse<paths['/api/search']>;
export type TvResponse = components['schemas']['TvResponse'];
export type MovieResponse = components['schemas']['MovieResponse'];

export function SearchComponent() {
  const { search } = useLocation();
  const query = new URLSearchParams(search.slice(1)).get('query')!;

  const {
    data: results,
    error,
    isValidating,
  } = useSWR<SearchResponse, Error>(['search', { query }]);

  return (
    <RouteTitle title="Search">
      <SearchBox />
      {error && <DisplayError error={error} />}
      <Loading loading={isValidating} />
      <ul>
        {results?.map((result) => (
          <li key={result.tmdb_id}>
            <MLink
              to={
                result.type === 'movie'
                  ? `/select/${result.tmdb_id}/options`
                  : `/select/${result.tmdb_id}/season`
              }
              state={{ query }}
            >
              <FontAwesomeIcon
                icon={result.type === 'movie' ? faTicketAlt : faTv}
              />
              &nbsp;
              {result.title} ({result.year ? result.year : 'Unknown year'})
            </MLink>
          </li>
        ))}
      </ul>
      {results && results.length === 0 ? 'No results' : null}
    </RouteTitle>
  );
}
