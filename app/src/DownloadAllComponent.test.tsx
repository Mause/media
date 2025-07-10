import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { renderWithSWR, mock, wait } from './test.utils';
import { DownloadAllComponent } from './DownloadAllComponent';
import type { ITorrent } from './OptionsComponent';

test('DownloadAllComponent', async () => {
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

  const packs: ITorrent[] = [
    {
      source: 'horriblesubs',
      category: 'Movie',
      download: 'magnet:....',
      episode_info: { seasonnum: 1, epnum: 1 },
      seeders: 5,
      title: 'Hello World',
    },
  ];

  await mock('/api/select/1/season/1/download_all', {
    packs,
    incomplete: [],
    complete: [],
  });
  await wait();

  expect(container).toMatchSnapshot();
});
