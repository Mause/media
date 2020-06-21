import React from 'react';
import { render } from '@testing-library/react';
import App from './App';
import { appUpdated, CallbackMountPoint } from './serviceWorkerCallback';
import { act } from 'react-dom/test-utils';

test('renders learn react link', () => {
  const el = render(<App />);
  expect(el.container).toMatchSnapshot();
});

test('renders app update notification', async () => {
  await act(async () => {
    render(<App />);
  });

  expect(CallbackMountPoint.onAppUpdate).toBeTruthy();

  expect(window.document.body).toMatchSnapshot();

  await act(async () => {
    appUpdated();
  });

  expect(
    window.document.body.getElementsByClassName('MuiAlert-message')[0],
  ).toHaveTextContent(
    'A new version of the app is available, please refresh to update!',
  );

  expect(window.document.body).toMatchSnapshot();
});
