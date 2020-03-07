import { act } from '@testing-library/react';
import React from 'react';
import { DownloadComponent, DownloadState } from './DownloadComponent';
import { Route, Router } from 'react-router-dom';
import { wait, useMoxios, renderWithSWR } from './test.utils';
import { createMemoryHistory } from 'history';
import moxios from 'moxios';

useMoxios();

test('DownloadComponent', async () => {
  await act(async () => {
    const history = createMemoryHistory();
    const state: DownloadState = {
      downloads: [
        {
          tmdb_id: '10000',
          magnet: '...',
        },
      ],
    };
    history.push('/download', state);

    const el = renderWithSWR(
      <Router history={history}>
        <Route path="/download">
          <DownloadComponent />
        </Route>
      </Router>,
    );

    expect(el.container).toMatchSnapshot();

    await moxios.stubOnce('POST', /\/api\/download/, {});
    await wait();

    expect(el.container).toMatchSnapshot();
    expect(history.length).toBe(2);
  });
});
