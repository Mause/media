import { act } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route } from 'react-router-dom';
import {
  EpisodeSelectComponent,
  Season,
  SeasonSelectComponent,
  TV,
} from './SeasonSelectComponent';
import { mock, usesMoxios, wait, renderWithSWR } from './test.utils';

usesMoxios();

test('SeasonSelectComponent  render', async () => {
  await act(async () => {
    const { getByTestId, container } = renderWithSWR(
      <MemoryRouter initialEntries={['/select/1/season']}>
        <Route path="/select/:tmdb_id/season">
          <SeasonSelectComponent />
        </Route>
      </MemoryRouter>,
    );

    await mock<TV>('/api/tv/1', {
      title: 'Hello',
      number_of_seasons: 1,
      seasons: [
        {
          season_number: 1,
          episode_count: 1,
        },
      ],
    });
    await wait();

    expect(getByTestId('title').textContent).toEqual('Hello');
    expect(container).toMatchSnapshot();
  });
});

test('EpisodeSelectComponent render', async () => {
  await act(async () => {
    const { container, getByTestId } = renderWithSWR(
      <MemoryRouter initialEntries={['/select/1/season/1']}>
        <Route path="/select/:tmdb_id/season/:season">
          <EpisodeSelectComponent />
        </Route>
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

    expect(getByTestId('title').textContent).toEqual('Season 1');
    expect(container).toMatchSnapshot();
  });
});
