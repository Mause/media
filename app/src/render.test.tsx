import { act, render } from '@testing-library/react';
import React from 'react';
import { Movies, TVShows } from './render';
import { Route, MemoryRouter } from 'react-router-dom';
import { mock, wait, useMoxios } from './test.utils';

useMoxios();

test('Movies', () => {
  const movies: Movie[] = [
    {
      id: 1,
      download: {
        title: 'Hello',
        added_by: {
          first_name: 'David',
        },
      },
    },
  ];

  const el = render(<Movies movies={movies} />);

  expect(el).toMatchSnapshot();
});

test('TVShows', async () => {
  await act(async () => {
    const series: TV[] = [
      {
        tmdb_id: 1,
        seasons: {
          1: [],
        },
      },
    ];
    const el = render(
      <MemoryRouter>
        <TVShows series={series} />
      </MemoryRouter>,
    );

    expect(el).toMatchSnapshot();
  });
});
