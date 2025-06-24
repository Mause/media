import ReactLoading from 'react-loading';
import { useLocation } from 'react-router-dom';
import useSWR from 'swr';

import * as qs from './qs';
import { SearchBox, DisplayError } from './IndexComponent';
import { MLink } from './utils';
import type { components } from './schema';
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
    <div>
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
    </div>
  );
}
