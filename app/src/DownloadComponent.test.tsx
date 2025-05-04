import { act, screen } from '@testing-library/react';
import React from 'react';
import { DownloadComponent, DownloadState } from './DownloadComponent';
import {
  Route,
  Routes,
  unstable_HistoryRouter as HistoryRouter,
} from 'react-router-dom';
import { wait, usesMoxios, renderWithSWR } from './test.utils';
import { createMemoryHistory } from '@remix-run/router';
import moxios from 'moxios';
import { expectLastRequestBody } from './utils';
import { listenTo } from './test.utils';

usesMoxios();

describe('DownloadComponent', () => {
  it('success', async () => {
    const history = createMemoryHistory();
    const entries = listenTo(history);
    const state: DownloadState = {
      downloads: [
        {
          tmdb_id: 10000,
          magnet: '...',
        },
      ],
    };
    history.push('/download', state);

    const { container } = renderWithSWR(
      <HistoryRouter history={history}>
        <Routes>
          <Route path="/download" Component={DownloadComponent} />
        </Routes>
      </HistoryRouter>,
    );

    expect(container).toMatchSnapshot();

    await moxios.stubOnce('POST', /\/api\/download/, {});
    expectLastRequestBody().toEqual([{ magnet: '...', tmdb_id: 10000 }]);
    await wait();

    expect(container).toMatchSnapshot();
    expect(entries.length).toBe(2);
  });
  it.skip('failure', async () => {
    const history = createMemoryHistory();
    const state: DownloadState = {
      downloads: [
        {
          tmdb_id: 10000,
          magnet: '...',
        },
      ],
    };
    history.push('/download', state);

    renderWithSWR(
      <HistoryRouter history={history}>
        <Route path="/download">
          <DownloadComponent />
        </Route>
      </HistoryRouter>,
    );

    await act(async () => {
      await moxios.stubFailure('POST', /\/api\/download/, {
        status: 500,
        response: { body: {}, message: 'an error has occured' },
      });
    });

    expect(await screen.findByTestId('errorMessage')).toHaveTextContent(
      'an error has occured',
    );
  });
});
