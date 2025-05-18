import React from 'react';
import ReactLoading from 'react-loading';
import qs from 'qs';
import { useLocation } from 'react-router-dom';
import { SearchBox } from './IndexComponent';
import useSWR from 'swr';
import { MLink } from './utils';
import { components } from './schema';
export type SearchResult = components['schemas']['SearchResponse'];

export function SearchComponent() {
  const { search } = useLocation();
  const { query } = qs.parse(search.slice(1));

  const { data: results } = useSWR<SearchResult[]>(
    'search?' + qs.stringify({ query }),
  );
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
