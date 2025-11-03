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

export class RequestWaiter {
  constructor() {
    this.requests = [];
    const listener = ({ request }: { request: Request }) => {
      this.requests.push(request);
    };
    server.events.on('request:end', listener);
  }
  async waitFor({nRequests = 1, timeout = 1000} : {nRequests: number, timeout: number}) {
    async function internal() {
      while (this.requests.length < nRequests) {
        await sleep(1);
      }
      server.events.removeListener('request:end', listener);
    }
    return await timeout(1000, internal());
  }
}

export async function waitForRequests(nRequests = 1): Promise<Request> {
  const waiter = new RequestWaiter();
  return await act<Request>(
    async () => waiter.waitFor({nRequests}),
  );
}
