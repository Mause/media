import React from 'react';
import ReactLoading from 'react-loading';
import qs from 'qs';
import { useLocation } from 'react-router-dom';
import { SearchBox } from './IndexComponent';
import useSWR from 'swr';
import { MLink } from './utils';

export interface SearchResult {
  Type: string;
  Year: number;
  imdbID: number;
  title: string;
}

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
          results.map(result => (
            <li key={result.imdbID}>
              <MLink
                to={{
                  pathname:
                    result.Type === 'movie'
                      ? `/select/${result.imdbID}/options`
                      : `/select/${result.imdbID}/season`,
                  state: { query },
                }}
              >
                {result.title} ({result.Year ? result.Year : 'Unknown year'})
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
