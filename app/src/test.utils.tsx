import type { Auth0ContextInterface } from '@auth0/auth0-react';
import { Auth0Context } from '@auth0/auth0-react';
import {
  createTheme,
  StyledEngineProvider,
  ThemeProvider,
} from '@mui/material/styles';
import { render } from '@testing-library/react';
import type { ReactElement } from 'react';
import { act } from 'react';
import { HelmetProvider } from 'react-helmet-async';
import { server } from './msw';
import { SwrConfigWrapper } from './streaming';

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

export async function waitForRequests(nRequests = 1): Promise<Request> {
  let remaining = nRequests;
  return await act<Request>(
    async () =>
      await Promise.race([
        new Promise<Request>((resolve) => {
          const listener = ({ request }: { request: Request }) => {
            if (--remaining > 0) return;
            server.events.removeListener('request:end', listener);
            resolve(request);
          };
          return server.events.on('request:end', listener);
        }),
        new Promise<Request>((resolve, reject) => {
          setTimeout(() => {
            reject(new Error('Timed out waiting for requests'));
          }, 1000);
        }),
      ]),
  );
}
