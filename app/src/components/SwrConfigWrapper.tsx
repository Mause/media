import { useAuth0 } from '@auth0/auth0-react';
import type { ReactNode } from 'react';
import { SWRConfig } from 'swr';

import { getToken, load } from '../utils';

export function SwrConfigWrapper({ children }: { children: ReactNode }) {
  const auth = useAuth0();
  return (
    <SWRConfig
      value={{
        // five minute refresh
        refreshInterval: 5 * 60 * 1000,
        fetcher: async (path: string | [string, object]) => {
          let params = undefined;
          if (Array.isArray(path)) {
            params = path[1];
            path = path[0];
          }
          return await load(
            path,
            params,
            auth.isAuthenticated
              ? {
                  Authorization: 'Bearer ' + (await getToken(auth)),
                }
              : {},
          );
        },
      }}
    >
      {children}
    </SWRConfig>
  );
}
