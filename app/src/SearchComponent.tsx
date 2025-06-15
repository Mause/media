import ReactLoading from 'react-loading';
import { useLocation } from 'react-router-dom';
import useSWR, { useSWRConfig } from 'swr';

import * as qs from './qs';
import { SearchBox } from './IndexComponent';
import { MLink } from './utils';
import type { components } from './schema';
export type SearchResult = components['schemas']['SearchResponse'];
export type TvResponse = components['schemas']['TvResponse'];
export type MovieResponse = components['schemas']['MovieResponse'];

export function SearchComponent() {
  const { search } = useLocation();
  const query = new URLSearchParams(search.slice(1)).get('query')!;
  const { mutate } = useSWRConfig();

  const { data: results } = useSWR<SearchResult[]>(
    'search?' + qs.stringify({ query }),
  );

  for (const result of results || []) {
    const prefix = result.type === 'movie' ? 'movie' : 'tv';
    const key = `${prefix}/${result.tmdb_id}`;
    if (prefix === 'movie') {
      void mutate(key, result satisfies MovieResponse);
    } else {
      void mutate(key, result satisfies TvResponse);
    }
  }

  return (
    <div>
      <SearchBox />
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
