import React from 'react';
import ReactLoading from 'react-loading';
import qs from 'qs';
import { Link, RouteComponentProps, withRouter } from 'react-router-dom';
import { useLoad } from './utils';

interface SearchResult {
  Type: string,
  Year: number,
  imdbID: number,
  title: string
}

export function _SearchComponent(props: RouteComponentProps<{}>) {
  const results = useLoad<SearchResult[]>('search', { query: getQuery(props) });
  return <div>
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

export function getQuery(props: RouteComponentProps<{}>) {
  return qs.parse(props.location.search.slice(1)).query;
}

const SearchComponent = withRouter(_SearchComponent);
export { SearchComponent };
