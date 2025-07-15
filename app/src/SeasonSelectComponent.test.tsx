import { screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { http, HttpResponse } from 'msw';

import type { Season, TV } from './SeasonSelectComponent';
import { SeasonSelectComponent } from './SeasonSelectComponent';
import { renderWithSWR, waitForRequests } from './test.utils';
import { EpisodeSelectComponent } from './EpisodeSelectComponent';
import { server } from './msw';

test('SeasonSelectComponent  render', async () => {
  const { container } = renderWithSWR(
    <MemoryRouter initialEntries={['/select/1/season']}>
      <Routes>
        <Route
          path="/select/:tmdb_id/season"
          Component={SeasonSelectComponent}
        />
      </Routes>
    </MemoryRouter>,
  );

  server.use(
    http.get('/api/tv/1', () =>
      HttpResponse.json({
        title: 'Hello',
        number_of_seasons: 1,
        imdb_id: null,
        seasons: [
          {
            season_number: 1,
            episode_count: 1,
          },
        ],
      } satisfies TV),
    ),
  );
  await waitForRequests();

  expect(screen.getByTestId('title').textContent).toEqual('Hello');
  expect(container).toMatchSnapshot();
});

test('EpisodeSelectComponent render', async () => {
  const { container } = renderWithSWR(
    <MemoryRouter initialEntries={['/select/1/season/1']}>
      <Routes>
        <Route
          path="/select/:tmdb_id/season/:season"
          Component={EpisodeSelectComponent}
        />
      </Routes>
    </MemoryRouter>,
  );

  server.use(
    http.get('/api/tv/1/season/1', () =>
      HttpResponse.json({
        episodes: [
          {
            episode_number: 1,
            id: 1,
            name: 'Episode 1',
          },
        ],
      } satisfies Season),
    ),
  );
  await waitForRequests();

  expect(screen.getByTestId('title').textContent).toEqual('Season 1');
  expect(container).toMatchSnapshot();
});
