import React from 'react';
import App from './App';
import { appUpdated, CallbackMountPoint } from './serviceWorkerCallback';
import { act } from 'react-dom/test-utils';
import { usesMoxios, renderWithSWR } from './test.utils';

usesMoxios();

test('renders learn react link', () => {
  const { container } = renderWithSWR(<App />);
  expect(container).toMatchSnapshot();
});

test('renders app update notification', async () => {
  renderWithSWR(<App />);

  expect(CallbackMountPoint.onAppUpdate).toBeTruthy();

  expect(getAlertMessage()).toBeFalsy();

  await act(async () => {
    appUpdated();
  });

  expect(getAlertMessage()).toHaveTextContent(
    'A new version of the app is available, please refresh to update!',
  );
});

function getAlertMessage(): Element | null {
  const messages =
    window.document.body.getElementsByClassName('MuiAlert-message');
  return messages.length ? messages[0] : null;
}
