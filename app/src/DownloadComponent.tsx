import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';

import { usePost, useLocation } from './utils';
import type { components } from './schema';
import { DisplayError } from './DisplayError';
import { Loading } from './render';
import { RouteTitle } from './RouteTitle';

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

  console.log({ done, error });

  let res: ReactNode;
  if (done) {
    res = <Navigate to="/" />;
  } else if (error) {
    res = <DisplayError error={error} />;
  } else {
    res = <Loading loading />;
  }

  return <RouteTitle title="Download">{res}</RouteTitle>;
}
