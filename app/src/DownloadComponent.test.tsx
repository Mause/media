import { screen } from '@testing-library/react';
import moxios from 'moxios';
import { act } from 'react';
import { Route, Routes, MemoryRouter } from 'react-router-dom';

import { wait, renderWithSWR, expectLastRequestBody } from './test.utils';
import type { DownloadState } from './DownloadComponent';
import { DownloadComponent } from './DownloadComponent';

describe('DownloadComponent', () => {
  it('success', async () => {
    const initialEntries = [
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
    ];

    const { container } = renderWithSWR(
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/" element={<div>Home</div>} />
          <Route path="/download" Component={DownloadComponent} />
        </Routes>
      </MemoryRouter>,
    );

    expect(container).toMatchSnapshot();

    await moxios.stubOnce('POST', /\/api\/download/, {});
    expectLastRequestBody().toEqual([{ magnet: '...', tmdb_id: 10000 }]);
    await wait();

    expect(container).toMatchSnapshot();
  });
  it.skip('failure', async () => {
    const initialEntries = [
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
    ];

    renderWithSWR(
      <MemoryRouter initialEntries={initialEntries}>
        <Route path="/download">
          <DownloadComponent />
        </Route>
      </MemoryRouter>,
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
