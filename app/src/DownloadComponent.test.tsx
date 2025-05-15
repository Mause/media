import { screen } from '@testing-library/react';
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
  it('failure', async () => {
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
    });

    const { container } = renderWithSWR(
      <HistoryRouter history={history}>
        <Routes>
          <Route path="/download" Component={DownloadComponent} />
        </Routes>
      </HistoryRouter>,
    );

    await moxios.stubFailure('POST', /\/api\/download/, {
      status: 500,
      response: { body: {}, message: 'an error has occured' },
    });
    await wait();

    expect(container).toMatchSnapshot();

    expect(await screen.findByTestId('errorMessage')).toHaveTextContent(
      'an error has occured',
    );
  });
});
