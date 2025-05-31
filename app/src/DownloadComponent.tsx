import ReactLoading from 'react-loading';
import { Navigate } from 'react-router-dom';

import { usePost, useLocation } from './utils';
import type { components } from './schema';
import { DisplayError } from './DisplayError';

export type DownloadCall = components['schemas']['DownloadPost'];
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
