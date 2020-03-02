import { useLocation, Redirect } from "react-router-dom";
import useSWR from 'swr';
import { TextField, Button, makeStyles, Theme, createStyles } from '@material-ui/core';
import React, { FormEvent, useState } from "react";

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
    setSubmitted(true)
  }

  const { state } = useLocation<{
    season?: number,
    episode?: number,
    tmdb_id: string,
  }>();

  const classes = useStyles();
  const { data } = useSWR<{ title: string }>(() => (state.season ? 'tv' : 'movie') + `/` + state.tmdb_id);
  const [magnet, setMagnet] = useState('');
  const [submitted, setSubmitted] = useState(false);

  if (!state) {
    return <Redirect to='/' />;
  }
  if (submitted) {
    return <Redirect to={{
      pathname: '/download', state: {
        magnet,
        ...state
      }
    }} />
  }

  return <form className={classes.root} onSubmit={onSubmit}>
    <h3>{data?.title}</h3>
    <TextField placeholder='magnet:...' onChange={e => setMagnet(e.target.value)} inputProps={{ pattern: '^magnet:.*' }} />
    <Button type="submit" variant='outlined'>Download</Button>
  </form>;
}
