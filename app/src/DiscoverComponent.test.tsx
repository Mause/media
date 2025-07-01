import moxios from 'moxios';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { wait, usesMoxios, renderWithSWR } from './test.utils';
import type { DiscoverResponse } from './DiscoveryComponent';
import { DiscoveryComponent } from './DiscoveryComponent';

usesMoxios();

test('DiscoveryComponent', async () => {
  const { container } = renderWithSWR(
    <MemoryRouter>
      <Routes>
        <Route
          index
          path="/"
          element={<DiscoveryComponent></DiscoveryComponent>}
        />
      </Routes>
    </MemoryRouter>,
  );

  expect(container).toMatchSnapshot();

  await moxios.stubOnce('GET', /api\/discover/, {
    status: 200,
    response: {
      results: [
        {
          id: 101,
          title: 'Machinist',
          overview: 'A man loses his mind',
          release_date: '2022-05-06',
          poster_path: '/hello.png',
        },
      ],
      page: 1,
      total_pages: 1,
      total_results: 1,
    } satisfies DiscoverResponse,
  });
  await wait();

  expect(container).toMatchSnapshot();
});
