import Search from '@mui/icons-material/Search';
import {
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  OutlinedInput,
} from '@mui/material';
import type { FormEvent } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import * as qs from './qs';

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
