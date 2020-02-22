import { act, render } from '@testing-library/react';
import React from 'react';
import { DownloadComponent, swrConfig } from './streaming';
import { Route, Router } from 'react-router-dom';
import { mock, wait, useMoxios } from './test.utils';
import { createMemoryHistory } from 'history';
import moxios from 'moxios';

useMoxios();

test('DownloadComponent', async () => {
  await act(async () => {
    const history = createMemoryHistory();
    const state = {
      tmdb_id: '10000',
      magnet: '...',
    };
    history.push('/download', state);

    const el = render(
      swrConfig(() => (
        <Router history={history}>
          <Route path="/download">
            <DownloadComponent />
          </Route>
        </Router>
      ))(),
    );

    expect(el).toMatchSnapshot();

    await moxios.stubOnce('POST', /\/api\/download/, {});
    await wait();

    expect(el).toMatchSnapshot();
    expect(history.length).toBe(2);
  });
});
