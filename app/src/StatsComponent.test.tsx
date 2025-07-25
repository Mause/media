import { http, HttpResponse } from 'msw';

import type { StatsResponse } from './StatsComponent';
import { StatsComponent } from './StatsComponent';
import { renderWithSWR, waitForRequests } from './test.utils';
import { server } from './msw';

test('render', async () => {
  const { container } = renderWithSWR(<StatsComponent />);

  server.use(
    http.get('/api/stats', () =>
      HttpResponse.json([
        { user: 'Mause', values: { episode: 1, movie: 1 } },
      ] satisfies StatsResponse[]),
    ),
  );
  await waitForRequests();

  expect(container).toMatchSnapshot();
});
