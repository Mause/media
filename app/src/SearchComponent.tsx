import ReactLoading from 'react-loading';
import { useLocation } from 'react-router-dom';
import useSWR from 'swr';

import * as qs from './qs';
import { DisplayError } from './DisplayError';
import { MLink } from './MLink';
import { SearchBox } from './SearchBox';
import type { components } from './schema';
import { RouteTitle } from './RouteTitle';
export type SearchResult = components['schemas']['SearchResponse'];

export function SearchComponent() {
  const { search } = useLocation();
  const query = new URLSearchParams(search.slice(1)).get('query')!;

  const {
    data: results,
    error,
    isValidating,
  } = useSWR<SearchResult[], Error>('search?' + qs.stringify({ query }));
  return (
    <RouteTitle title="Search">
      <SearchBox />
      {error && <DisplayError error={error} />}
      {isValidating && <ReactLoading type="balls" color="#000" />}
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
              {result.title} ({result.year ? result.year : 'Unknown year'})
            </MLink>
          </li>
        ))}
      </ul>
      {results && results.length === 0 ? 'No results' : null}
    </RouteTitle>
  );
}
