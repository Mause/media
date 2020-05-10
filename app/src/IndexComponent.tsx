import React, { FormEvent, useState } from 'react';
import { TVShows, Movies } from './render';
import { IndexResponse, Torrents } from './streaming';
import { useHistory } from 'react-router-dom';
import qs from 'qs';
import useSWR from 'swr';
import { Alert } from '@material-ui/lab';
import _ from 'lodash';

const CFG = {
  refreshInterval: 10000,
};
function IndexComponent() {
  const { data: state, isValidating: loadingState } = useSWR<IndexResponse>(
    'index',
    CFG,
  );
  const { data: torrents, isValidating: loadingTorrents, error } = useSWR<
    Torrents
  >('torrents', CFG);

  const loading = loadingState || loadingTorrents;

  const ostate = state || { series: [], movies: [] };

  return (
    <div>
      <SearchBox />
      {error && <DisplayError error={error} />}
      <Movies torrents={torrents} movies={ostate.movies} loading={loading} />
      <TVShows torrents={torrents} series={ostate.series} loading={loading} />
    </div>
  );
}

export function DisplayError(props: { error: Error }) {
  let message = 'Unable to connect to transmission: ' + props.error.toString();

  if ((props.error as any).isAxiosError) {
    message = _.get(props.error, 'response.data.message') || message;
  }

  return (
    <div>
      <br />
      <Alert color="warning">{message}</Alert>
    </div>
  );
}

export function SearchBox() {
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    history.push({ pathname: '/search', search: qs.stringify({ query }) });
  }

  const [query, setQuery] = useState('');
  const history = useHistory();

  return (
    <form onSubmit={search}>
      <input name="query" onChange={e => setQuery(e.target.value)} />
      &nbsp;
      <input type="submit" value="Search" />
    </form>
  );
}

export { IndexComponent };
