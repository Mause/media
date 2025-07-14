import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { http, HttpResponse } from 'msw';

import { renderWithSWR, waitForRequests } from './test.utils';
import { DownloadAllComponent } from './DownloadAllComponent';
import type { ITorrent } from './OptionsComponent';
import { server } from './msw';

test('DownloadAllComponent', async () => {
  server.use(
    http.get('/api/select/1/season/1/download_all', () =>
      HttpResponse.json({
        packs: [
          {
            source: 'horriblesubs',
            category: 'Movie',
            download: 'magnets://?xt=hello',
            episode_info: { seasonnum: 1, epnum: 1 },
            seeders: 5,
            title: 'Hello World',
          },
        ] satisfies ITorrent[],
        incomplete: [],
        complete: [],
      }),
    ),
  );
  server.use(http.get('/api/tv/1', () => HttpResponse.json({})));
  server.use(http.get('/api/torrents', () => HttpResponse.json({})));

  const { container } = renderWithSWR(
    <MemoryRouter initialEntries={['/select/1/season/1/download_all']}>
      <Routes>
        <Route
          path="/select/:tmdb_id/season/:season/download_all"
          Component={DownloadAllComponent}
        />
      </Routes>
    </MemoryRouter>,
  );

  expect(container).toMatchSnapshot();

  await waitForRequests();

  expect(container).toMatchSnapshot();
});
