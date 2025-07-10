import { Route, MemoryRouter, Routes } from 'react-router-dom';

import type { SearchResponse } from './SearchComponent';
import { SearchComponent } from './SearchComponent';
import { mock, wait, renderWithSWR } from './test.utils';

test('SearchComponent', async () => {
  const { container } = renderWithSWR(
    <MemoryRouter initialEntries={['/search?query=world']}>
      <Routes>
        <Route path="/search" Component={SearchComponent} />
      </Routes>
    </MemoryRouter>,
  );

  const results: SearchResponse = [
    {
      type: 'movie',
      tmdb_id: 10000,
      year: 2019,
      title: 'Hello',
    },
  ];
  await mock('/api/search?query=world', results);
  await wait();

  expect(container).toMatchSnapshot();
});
