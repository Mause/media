import { screen } from '@testing-library/react';
import {
  Route,
  Routes,
  unstable_HistoryRouter as HistoryRouter,
} from 'react-router-dom';
import { createMemoryHistory } from '@remix-run/router';
import moxios from 'moxios';
import { act } from 'react';

import {
  wait,
  usesMoxios,
  renderWithSWR,
  listenTo,
  expectLastRequestBody,
} from './test.utils';
import type { DownloadState } from './DownloadComponent';
import { DownloadComponent } from './DownloadComponent';

usesMoxios();

describe('DownloadComponent', () => {
  it('success', async () => {
    const history = createMemoryHistory({
      initialEntries: [
        {
          pathname: '/download',
          state: {
            downloads: [
              {
                tmdb_id: 10000,
                magnet: '...',
              },
            ],
          } satisfies DownloadState,
        },
      ],
      v5Compat: true,
    });
    const entries = listenTo(history);

    const { container } = renderWithSWR(
      <HistoryRouter history={history}>
        <Routes>
          <Route path="/" element={<div>Home</div>} />
          <Route path="/download" Component={DownloadComponent} />
        </Routes>
      </HistoryRouter>,
    );

    expect(container).toMatchSnapshot();

    await moxios.stubOnce('POST', /\/api\/download/, {});
    expectLastRequestBody().toEqual([{ magnet: '...', tmdb_id: 10000 }]);
    await wait();

    expect(container).toMatchSnapshot();
    expect(entries.map((e) => e.pathname)).toEqual(['/']);
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
