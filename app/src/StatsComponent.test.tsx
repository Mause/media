import type { StatsResponse } from './StatsComponent';
import { StatsComponent } from './StatsComponent';
import { mock, renderWithSWR, wait } from './test.utils';

test('render', async () => {
  const { container } = renderWithSWR(<StatsComponent />);

  await mock<StatsResponse[]>('/api/stats', [
    { user: 'Mause', values: { episode: 1, movie: 1 } },
  ]);
  await wait();

  expect(container).toMatchSnapshot();
});
