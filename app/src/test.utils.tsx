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
import * as _ from 'lodash-es';

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
  requests: Request[];
  listener: ({ request }: { request: Request }) => void;

  constructor() {
    this.requests = [];
    this.listener = ({ request }: { request: Request }) => {
      this.requests.push(request);
    };
    server.events.on('request:end', this.listener);
  }

  async waitFor({
    nRequests = 1,
    timeoutMs = 1000,
  }: {
    nRequests?: number;
    timeoutMs?: number;
  } = {}): Promise<Request> {
    const internal = async () => {
      while (this.requests.length < nRequests) {
        await sleep(1);
      }
      server.events.removeListener('request:end', this.listener);
    };
    await act(() => timeout(timeoutMs, internal()));
    return _.last(this.requests)!;
  }
}

export async function waitForRequests(nRequests = 1): Promise<Request> {
  const waiter = new RequestWaiter();
  return await waiter.waitFor({ nRequests });
}
