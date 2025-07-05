import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { wait, usesMoxios, renderWithSWR, mock } from './test.utils';
import type { Configuration, DiscoverResponse } from './DiscoveryComponent';
import { DiscoveryComponent } from './DiscoveryComponent';

usesMoxios();

test('DiscoveryComponent', async () => {
  const { container } = renderWithSWR(
    <MemoryRouter>
      <Routes>
        <Route index path="/" element={<DiscoveryComponent />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(container).toMatchSnapshot();

  await Promise.all([
    mock('/api/discover', {
      results: [
        {
          id: 101,
          title: 'Machinist',
          overview: 'A man loses his mind',
          release_date: '2022-05-06',
          poster_path: '/hello.png',
        },
      ],
    } satisfies DiscoverResponse),
    mock('/api/tmdb/configuration', {
      images: {
        backdrop_sizes: [],
        base_url: 'https://tmdb.org/',
        logo_sizes: [],
        poster_sizes: ['w800', 'original'],
        profile_sizes: [],
        secure_base_url: 'https://tmdb.org/',
        still_sizes: [],
      },
      change_keys: [],
    } as Configuration),
  ]);
  await wait();

  expect(container).toMatchSnapshot();
});
