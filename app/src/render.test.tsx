import { act, render } from '@testing-library/react';
import React from 'react';
import { Movies, TVShows } from './render';
import { Route, MemoryRouter } from 'react-router-dom';
import { mock, wait, useMoxios } from './test.utils';
import { MovieResponse } from './streaming';
import { TvResponse } from './types';

useMoxios();

test('Movies', () => {
  const movies: MovieResponse[] = [
    {
      id: 1,
      download: {
        title: 'Hello',
        added_by: {
          first_name: 'David',
        },
        id: 1,
        imdb_id: '',
        transmission_id: '',
      },
    },
  ];

  const el = render(<Movies movies={movies} loading={false} />);

  expect(el).toMatchSnapshot();
});

test('TVShows', async () => {
  await act(async () => {
    const series: SeriesResponse[] = [
      {
        tmdb_id: 1,
        seasons: {
          1: [],
        },
      },
    ];
    const el = render(
      <MemoryRouter>
        <TVShows series={series} loading={false} />
      </MemoryRouter>,
    );

    expect(el).toMatchSnapshot();
  });
});
