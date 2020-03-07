import React from 'react';
import ReactLoading from 'react-loading';
import { Redirect } from 'react-router';
import { useLocation } from 'react-router-dom';
import { usePost } from './utils';

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
  const { state } = useLocation<{ download: DownloadCall[] }>();

  const [done] = usePost('download', state.download);

  return done ? <Redirect to="/" /> : <ReactLoading color="#000000" />;
}
