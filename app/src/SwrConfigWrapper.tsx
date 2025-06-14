import { useAuth0 } from '@auth0/auth0-react';
import type { ReactNode } from 'react';
import type { Cache } from 'swr';
import { SWRConfig } from 'swr';

import { getToken, load } from './utils';

function localStorageProvider(): Cache {
  // When initializing, we restore the data from `localStorage` into a map.
  const map = new Map(JSON.parse(localStorage.getItem('app-cache') || '[]'));

  // Before unloading the app, we write back all the data into `localStorage`.
  window.addEventListener('beforeunload', () => {
    const appCache = JSON.stringify(Array.from(map.entries()));
    localStorage.setItem('app-cache', appCache);
  });

  // We still use the map for write & read for performance.
  return map as Cache;
}

export function SwrConfigWrapper({
  children,
  cache,
}: {
  children: ReactNode;
  cache?: Cache;
}) {
  const auth = useAuth0();
  return (
    <SWRConfig
      value={{
        // five minute refresh
        refreshInterval: 5 * 60 * 1000,
        fetcher: async (path: string, params: string) =>
          await load(
            path,
            params,
            auth.isAuthenticated
              ? {
                  Authorization: 'Bearer ' + (await getToken(auth)),
                }
              : {},
          ),
        provider: cache ? () => cache : localStorageProvider,
      }}
    >
      {children}
    </SWRConfig>
  );
}
