import { MemoryRouter, Route, Routes } from 'react-router-dom';

import type { SearchResult } from './SearchComponent';
import { SearchComponent } from './SearchComponent';
import { mock, renderWithSWR, usesMoxios, wait } from './test.utils';

usesMoxios();

test('SearchComponent', async () => {
  const { container } = renderWithSWR(
    <MemoryRouter initialEntries={['/search?query=world']}>
      <Routes>
        <Route path="/search" Component={SearchComponent} />
      </Routes>
    </MemoryRouter>,
  );

  const results: SearchResult[] = [
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
