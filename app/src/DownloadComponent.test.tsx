import { screen } from '@testing-library/react';
import { Route, Routes, MemoryRouter } from 'react-router-dom';
import axios from 'axios';
import moxios from 'moxios';
import { HttpResponse, http } from 'msw';

import { renderWithSWR, waitForRequests } from './test.utils';
import type { DownloadCall, DownloadState } from './DownloadComponent';
import { DownloadComponent } from './DownloadComponent';
import { server } from './msw';
import { paths } from './schema';

type DownloadResponse =
  paths['/api/download']['post']['responses']['200']['content']['application/json'];

describe('DownloadComponent', () => {
  it('success', async () => {
    moxios.uninstall(axios);
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

    let body: DownloadCall[] | undefined = undefined;
    server.use(
      http.post('/api/download', async ({ request }) => {
        body = (await request.json()) as DownloadCall[];
        return HttpResponse.json([
          {
            id: 12345,
            download: {
              tmdb_id: 10000,
              transmission_id: '12345',
              id: 12345,
              imdb_id: 'tt1234567',
              type: 'movie',
              title: 'Test Movie',
              timestamp: '2023-10-01T00:00:00Z',
              added_by: {
                username: 'testuser',
                first_name: 'Test',
              },
            },
          },
        ] satisfies DownloadResponse);
      }),
    );

    const { container } = renderWithSWR(
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/" element={<div>Home</div>} />
          <Route path="/download" Component={DownloadComponent} />
        </Routes>
      </MemoryRouter>,
    );

    expect(container).toMatchSnapshot();

    await waitForRequests();
    expect(body).toEqual([{ magnet: '...', tmdb_id: 10000 }]);

    expect(container).toMatchSnapshot();
  });
  it.skip('failure', async () => {
    moxios.uninstall(axios);
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

    server.use(http.post('/api/download', () => HttpResponse.error()));
    await waitForRequests();

    expect(await screen.findByTestId('errorMessage')).toHaveTextContent(
      'an error has occured',
    );
  });
});
