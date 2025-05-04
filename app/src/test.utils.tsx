import React from 'react';
import moxios from 'moxios';
import { swrConfig } from './streaming';
import { render, act } from '@testing-library/react';
import { ReactElement } from 'react';
import { Auth0Context, Auth0ContextInterface } from '@auth0/auth0-react';
import {
  ThemeProvider,
  StyledEngineProvider,
  createTheme,
} from '@mui/material/styles';
import { Location, MemoryHistory } from '@remix-run/router';

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
        <ThemeProvider theme={theme}>{swrConfig(() => el)()}</ThemeProvider>
      </StyledEngineProvider>
    </Auth0Context.Provider>,
  );
}

export function usesMoxios() {
  beforeEach(() => {
    moxios.install();
  });
  afterEach(() => {
    moxios.uninstall();
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
