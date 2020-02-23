import React from 'react';
import ReactLoading from 'react-loading';
import qs from 'qs';
import { useLocation, Link } from 'react-router-dom';
import { useLoad } from './utils';
import { SearchBox } from './IndexComponent';

interface SearchResult {
  Type: string,
  Year: number,
  imdbID: number,
  title: string
}

export function SearchComponent() {
  const { search } = useLocation();
  const { query } = qs.parse(search.slice(1));

  const results = useLoad<SearchResult[]>('search', { query, });
  return <div>
    <SearchBox />
    <ul>
      {results ? results.map(result => <li key={result.imdbID}>
        <Link to={result.Type === 'movie' ?
          `/select/${result.imdbID}/options` :
          `/select/${result.imdbID}/season`}>{result.title} ({result.Year ? result.Year : 'Unknown year'})</Link>
      </li>) : <ReactLoading type='balls' color='#000' />}
    </ul>
    {results && results.length === 0 ?
      'No results' : null}
  </div>;
}
