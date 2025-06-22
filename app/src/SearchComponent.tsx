import ReactLoading from 'react-loading';
import { useLocation } from 'react-router-dom';
import useSWR from 'swr';

import * as qs from './qs';
import { SearchBox } from './IndexComponent';
import { MLink } from './utils';
import type { components } from './schema';
export type SearchResult = components['schemas']['SearchResponse'];
import { DisplayError } from './IndexComponent';

export function SearchComponent() {
  const { search } = useLocation();
  const query = new URLSearchParams(search.slice(1)).get('query')!;

  const { data: results, error } = useSWR<SearchResult[]>(
    'search?' + qs.stringify({ query }),
  );
  return (
    <div>
      <SearchBox />
      {error && <DisplayError error={error} />}
      <ul>
        {results ? (
          results.map((result) => (
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
          ))
        ) : (
          <ReactLoading type="balls" color="#000" />
        )}
      </ul>
      {results && results.length === 0 ? 'No results' : null}
    </div>
  );
}
