import moxios from 'moxios';
import axios from 'axios';
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
import type { Location, MemoryHistory } from '@remix-run/router';
import type { Listener } from '@remix-run/router/dist/history';
import { HelmetProvider } from 'react-helmet-async';

import { SwrConfigWrapper } from './streaming';

const theme = createTheme();

export async function wait() {
  return await act(
    async () => await new Promise<void>((resolve) => moxios.wait(resolve)),
  );
}

export async function mock<T>(path: string, response: T) {
  await moxios.stubOnce('GET', new RegExp(path.replace(/\?/, '\\?')), {
    response,
  });
}

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
          <HelmetProvider>
            <SwrConfigWrapper>{el}</SwrConfigWrapper>
          </HelmetProvider>
        </ThemeProvider>
      </StyledEngineProvider>
    </Auth0Context.Provider>,
  );
}

export function usesMoxios() {
  beforeEach(() => {
    moxios.install(axios);
  });
  afterEach(() => {
    moxios.uninstall(axios);
  });
}

export function listenTo(hist: MemoryHistory) {
  const entries: Location[] = [];
  const otherListeners: Listener[] = [];
  hist.listen((hist) => {
    entries.push(hist.location);
    for (const listener of otherListeners) {
      listener(hist);
    }
  });
  hist.listen = (listener) => {
    otherListeners.push(listener);
    return () => {};
  };
  return entries;
}

export function expectLastRequestBody() {
  const mr = moxios.requests.mostRecent();
  expect(mr).toBeTruthy();
  return expect(JSON.parse(mr.config.data as string));
}
