import React from 'react';
import ReactLoading from 'react-loading';
import { Navigate } from 'react-router-dom';
import { usePost, useLocation } from './utils';
import { DisplayError } from './IndexComponent';

export interface DownloadCall {
  tmdb_id: string;
  magnet: string;
  season?: string;
  episode?: string;
}
export interface DownloadState {
  downloads: DownloadCall[];
}

export function DownloadComponent() {
  const { state } = useLocation<DownloadState>();

  const { done, error } = usePost(
    'download',
    state.downloads.map((item: DownloadCall) => ({
      ...item,
      tmdb_id: Number(item.tmdb_id),
    })),
  );

  if (error) {
    return <DisplayError error={error} />;
  }

  return done ? <Navigate to="/" /> : <ReactLoading color="#000000" />;
}
