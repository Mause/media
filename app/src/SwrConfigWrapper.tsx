import { useAuth0 } from '@auth0/auth0-react';
import type { ReactNode } from 'react';
import type { Cache } from 'swr';
import { SWRConfig } from 'swr';

import { getToken, load } from './utils';

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
        provider: () => cache || new Map(),
      }}
    >
      {children}
    </SWRConfig>
  );
}
