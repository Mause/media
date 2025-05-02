import React from 'react';
import { SearchComponent, SearchResult } from './SearchComponent';
import { Route, MemoryRouter } from 'react-router-dom';
import { mock, wait, usesMoxios, renderWithSWR } from './test.utils';

usesMoxios();

test('SearchComponent', async () => {
  const { container } = renderWithSWR(
    <MemoryRouter initialEntries={['/search?query=world']}>
      <Route path="/search">
        <SearchComponent />
      </Route>
    </MemoryRouter>,
  );

  const results: SearchResult[] = [
    {
      type: 'movie',
      imdbID: 10000,
      year: 2019,
      title: 'Hello',
    },
  ];
  await mock('/api/search?query=world', results);
  await wait();

  expect(container).toMatchSnapshot();
});
