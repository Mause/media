import { render } from '@testing-library/react';
import type { ReactElement } from 'react';
import { act } from 'react';
import type { Auth0ContextInterface } from '@auth0/auth0-react';
import { Auth0Context } from '@auth0/auth0-react';
import {
  ThemeProvider,
  StyledEngineProvider,
  createTheme,
} from '@mui/material/styles';

import { SwrConfigWrapper } from './components';
import { server } from './msw';

const theme = createTheme();

export function renderWithSWR(el: ReactElement) {
  const c = {
    isAuthenticated: true,
    getAccessTokenSilently() {
      return Promise.resolve('TOKEN');
    },
  } as Auth0ContextInterface;
  return render(
    <Auth0Context.Provider value={c}>
      <StyledEngineProvider injectFirst>
        <ThemeProvider theme={theme}>
          <SwrConfigWrapper>{el}</SwrConfigWrapper>
        </ThemeProvider>
      </StyledEngineProvider>
    </Auth0Context.Provider>,
  );
}

const sleep = async (ms: number) =>
  await new Promise<void>((resolve) => {
    setTimeout(() => {
      resolve();
    }, ms);
  });
const errorIn = async (ms: number) => {
  await sleep(ms);
  throw new Error('Timed out waiting for requests');
};
export async function timeout<T>(ms: number, promise: Promise<T>) {
  return await Promise.race([promise, errorIn(ms)]);
}

export async function waitForRequests(nRequests = 1): Promise<Request> {
  let remaining = nRequests;
  return await act<Request>(
    async () =>
      await timeout<Request>(
        1000,
        new Promise<Request>((resolve) => {
          const listener = ({ request }: { request: Request }) => {
            if (--remaining > 0) return;
            server.events.removeListener('request:end', listener);
            resolve(request);
          };
          return server.events.on('request:end', listener);
        }),
      ),
  );
}
