import { act } from '@testing-library/react';
import React from 'react';
import { SearchComponent, SearchResult } from './SearchComponent';
import { Route, MemoryRouter } from 'react-router-dom';
import { mock, wait, useMoxios, renderWithSWR } from './test.utils';

useMoxios();

test('SearchComponent', async () => {
  await act(async () => {
    const el = renderWithSWR(
      <MemoryRouter initialEntries={['/search?query=world']}>
        <Route path="/search">
          <SearchComponent />
        </Route>
      </MemoryRouter>,
    );

    const results: SearchResult[] = [
      {
        Type: 'movie',
        imdbID: 10000,
        Year: 2019,
        title: 'Hello',
      },
    ];
    await mock('/api/search?query=world', results);
    await wait();

    expect(el.container).toMatchSnapshot();
  });
});
