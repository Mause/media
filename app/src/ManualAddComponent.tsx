import { Navigate } from 'react-router-dom';
import { styled } from '@mui/material/styles';
import useSWR from 'swr';
import { TextField, Button } from '@mui/material';
import { FormEvent, useState } from 'react';

import { DownloadState } from './DownloadComponent';
import { useLocation } from './utils';

const PREFIX = 'ManualAddComponent';

const classes = {
  root: `${PREFIX}-root`,
};

const Root = styled('form')(({ theme }) => ({
  [`&.${classes.root}`]: {
    '& > *': {
      margin: theme.spacing(1),
    },
  },
}));

export function ManualAddComponent() {
  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitted(true);
  }

  const { state: state_s } = useLocation<{
    season?: string;
    episode?: string;
    tmdb_id: string;
  }>();
  const state = {
    season: state_s?.season ? parseInt(state_s.season) : undefined,
    episode: state_s?.episode ? parseInt(state_s.episode) : undefined,
    tmdb_id: state_s.tmdb_id,
  };

  const { data } = useSWR<{ title: string }>(
    () => (state.season ? 'tv' : 'movie') + `/` + state.tmdb_id,
  );
  const [magnet, setMagnet] = useState('');
  const [submitted, setSubmitted] = useState(false);

  if (!state) {
    return <Navigate to="/" />;
  }
  if (submitted) {
    const toState: DownloadState = {
      downloads: [
        {
          magnet,
          ...state,
          tmdb_id: parseInt(state.tmdb_id),
        },
      ],
    };
    return <Navigate to="/download" state={toState} />;
  }

  return (
    <Root className={classes.root} onSubmit={onSubmit}>
      <h3>{data?.title}</h3>
      <TextField
        variant="standard"
        placeholder="magnet:..."
        onChange={(e) => setMagnet(e.target.value)}
        slotProps={{
          htmlInput: { pattern: '^magnet:.*' },
        }}
      />
      <Button type="submit" variant="outlined">
        Download
      </Button>
    </Root>
  );
}
