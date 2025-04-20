import { useLocation, Redirect } from 'react-router-dom';
import useSWR from 'swr';
import { TextField, Button, Theme } from '@mui/material';
import makeStyles from '@mui/styles/makeStyles';
import createStyles from '@mui/styles/createStyles';
import { DownloadState } from './DownloadComponent';
import React, { FormEvent, useState } from 'react';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      '& > *': {
        margin: theme.spacing(1),
      },
    },
  }),
);

export function ManualAddComponent() {
  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitted(true);
  }

  const { state } = useLocation<{
    season?: string;
    episode?: string;
    tmdb_id: string;
  }>();

  const classes = useStyles();
  const { data } = useSWR<{ title: string }>(
    () => (state.season ? 'tv' : 'movie') + `/` + state.tmdb_id,
  );
  const [magnet, setMagnet] = useState('');
  const [submitted, setSubmitted] = useState(false);

  if (!state) {
    return <Redirect to="/" />;
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
    return <Redirect to={{ pathname: '/download', state: toState }} />;
  }

  return (
    <form className={classes.root} onSubmit={onSubmit}>
      <h3>{data?.title}</h3>
      <TextField
        placeholder="magnet:..."
        onChange={(e) => setMagnet(e.target.value)}
        inputProps={{ pattern: '^magnet:.*' }}
      />
      <Button type="submit" variant="outlined">
        Download
      </Button>
    </form>
  );
}
