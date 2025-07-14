import { HttpResponse, http } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { server } from './msw';
import type { SearchResponse } from './SearchComponent';
import { SearchComponent } from './SearchComponent';
import { renderWithSWR, waitForRequests } from './test.utils';

test('SearchComponent', async () => {
  server.use(
    http.get('/api/search', ({ request }) => {
      expect(new URL(request.url).search).toEqual('?query=world');
      return HttpResponse.json([
        {
          type: 'movie',
          tmdb_id: 10000,
          year: 2019,
          title: 'Hello',
        },
      ] satisfies SearchResponse);
    }),
  );

  const { container } = renderWithSWR(
    <MemoryRouter initialEntries={['/search?query=world']}>
      <Routes>
        <Route path="/search" Component={SearchComponent} />
      </Routes>
    </MemoryRouter>,
  );

  await waitForRequests();

  expect(container).toMatchSnapshot();
});
