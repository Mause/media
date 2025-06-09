import { screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import {
  EpisodeSelectComponent,
  Season,
  SeasonSelectComponent,
  TV,
} from './SeasonSelectComponent';
import { mock, usesMoxios, wait, renderWithSWR } from './test.utils';

usesMoxios();

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

  await mock<TV>('/api/tv/1', {
    title: 'Hello',
    number_of_seasons: 1,
    imdb_id: null,
    seasons: [
      {
        season_number: 1,
        episode_count: 1,
      },
    ],
  });
  await wait();

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

  await mock<Season>('/api/tv/1/season/1', {
    episodes: [
      {
        episode_number: 1,
        id: 1,
        name: 'Episode 1',
      },
    ],
  });
  await wait();

  expect(screen.getByTestId('title').textContent).toEqual('Season 1');
  expect(container).toMatchSnapshot();
});
