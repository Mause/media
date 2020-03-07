import React from 'react';
import ReactLoading from 'react-loading';
import { Redirect } from 'react-router';
import { useLocation } from 'react-router-dom';
import { usePost } from './utils';

export function DownloadComponent() {
  const { state } = useLocation<{
    tmdb_id: string;
    magnet: string;
    season?: string;
    episode?: string;
  }>();
  const [done] = usePost('download', [
    {
      tmdb_id: state!.tmdb_id,
      magnet: state.magnet,
      season: state.season,
      episode: state.episode,
    },
  ]);
  return done ? <Redirect to="/" /> : <ReactLoading color="#000000" />;
}
