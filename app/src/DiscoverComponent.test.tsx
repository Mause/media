import { MemoryRouter, Route, Routes } from 'react-router-dom';
import moxios from 'moxios';
import axios from 'axios';
import { http, HttpResponse } from 'msw';

import { renderWithSWR } from './test.utils';
import type { Configuration, DiscoverResponse } from './DiscoveryComponent';
import { DiscoveryComponent } from './DiscoveryComponent';
import { server } from './msw';

test('DiscoveryComponent', () => {
  moxios.uninstall(axios);

  const { container } = renderWithSWR(
    <MemoryRouter>
      <Routes>
        <Route index path="/" element={<DiscoveryComponent />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(container).toMatchSnapshot();

  server.use(
    http.get('/api/discover', () =>
      HttpResponse.json({
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
    ),
  );
  server.use(
    http.get('/api/tmdb/configuration', () =>
      HttpResponse.json({
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
    ),
  );

  expect(container).toMatchSnapshot();
});
