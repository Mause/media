import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { http, HttpResponse } from 'msw';

import { renderWithSWR, waitForRequests } from './test.utils';
import type { ManualAddComponentState } from './ManualAddComponent';
import ManualAddComponent from './ManualAddComponent';
import { server } from './msw';

it('works', async () => {
  const { container } = renderWithSWR(
    <MemoryRouter
      initialEntries={[
        {
          pathname: '/',
          state: {
            tmdb_id: '12345',
            season: '1', // optional, for TV shows
          } satisfies ManualAddComponentState,
        },
      ]}
    >
      <Routes>
        <Route path="/" Component={ManualAddComponent} />
      </Routes>
    </MemoryRouter>,
  );

  expect(container).toMatchSnapshot();

  server.use(
    http.get('/api/tv/12345', () =>
      HttpResponse.json({
        title: 'Test TV Show',
      }),
    ),
  );
  await waitForRequests();

  expect(container).toMatchSnapshot();
});
