import type { FormEvent } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useSWR from 'swr';
import {
  FormControl,
  OutlinedInput,
  IconButton,
  InputLabel,
  InputAdornment,
} from '@mui/material';
import Search from '@mui/icons-material/Search';
import * as _ from 'lodash-es';

import * as qs from './qs';
import type { IndexResponse, Torrents } from './streaming';
import { TVShows, Movies } from './render';
import { DisplayError } from './DisplayError';

const CFG = {
  refreshInterval: 10000,
};
function IndexComponent() {
  const { data: state, isValidating: loadingState } = useSWR<IndexResponse>(
    'index',
    CFG,
  );
  const {
    data: torrents,
    isValidating: loadingTorrents,
    error,
  } = useSWR<Torrents, Error>('torrents', CFG);

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

export function SearchBox() {
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void navigate({ pathname: '/search', search: qs.stringify({ query }) });
  }

  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  return (
    <form onSubmit={search}>
      <FormControl sx={{ m: 1, width: '25ch' }} variant="outlined">
        <InputLabel htmlFor="outlined-adornment-search">Search</InputLabel>
        <OutlinedInput
          id="outlined-adornment-search"
          type="text"
          size="small"
          onChange={(e) => setQuery(e.target.value)}
          endAdornment={
            <InputAdornment position="end">
              <IconButton aria-label="search" type="submit" edge="end">
                <Search />
              </IconButton>
            </InputAdornment>
          }
          label="Search"
        />
      </FormControl>
    </form>
  );
}

export { IndexComponent };
