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
          <HelmetProvider>
            <SwrConfigWrapper>{el}</SwrConfigWrapper>
          </HelmetProvider>
        </ThemeProvider>
      </StyledEngineProvider>
    </Auth0Context.Provider>,
  );
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

export async function waitForRequests() {
  await act(async () => {
    await Promise.race([
      new Promise<void>((resolve) => {
        const listener = () => {
          server.events.removeListener('request:end', listener);
          resolve();
        };
        return server.events.on('request:end', listener);
      }),
      new Promise((resolve, reject) => {
        setTimeout(() => {
          reject(new Error('Timed out waiting for requests'));
        }, 1000);
      }),
    ]);
  });
}
