import React from 'react';
import { swrConfig } from './streaming';
import { render, act } from '@testing-library/react';
import { ReactElement } from 'react';
import { Auth0Context, Auth0ContextInterface } from '@auth0/auth0-react';
import {
  ThemeProvider,
  StyledEngineProvider,
  createTheme,
} from '@mui/material/styles';

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
        <ThemeProvider theme={theme}>{swrConfig(() => el)()}</ThemeProvider>
      </StyledEngineProvider>
    </Auth0Context.Provider>,
  );
}
