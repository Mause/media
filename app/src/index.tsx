import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import * as serviceWorker from './serviceWorker';
// import { appUpdated } from './serviceWorkerCallback';
import { Auth0Provider } from '@auth0/auth0-react';

import {
  ThemeProvider,
  Theme,
  StyledEngineProvider,
  createTheme,
} from '@mui/material/styles';

declare module '@mui/styles/defaultTheme' {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface DefaultTheme extends Theme {}
}

const theme = createTheme();

const clientId = process.env.REACT_APP_AUTH0_CLIENT_ID;
const audience = process.env.REACT_APP_AUTH0_AUDIENCE;

if (!(clientId && audience)) {
  console.error(
    'Missing Auth0 client ID or audience. Please check your environment variables.',
  );
}

ReactDOM.render(
  <Auth0Provider
    domain="mause.au.auth0.com"
    clientId={clientId}
    audience={audience}
    useRefreshTokens={true}
    redirectUri={window.location.origin}
    cacheLocation="localstorage"
  >
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={theme}>
        <App />
      </ThemeProvider>
    </StyledEngineProvider>
  </Auth0Provider>,
  document.getElementById('root'),
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
// serviceWorker.register({ onUpdate: appUpdated });
