import React from 'react';
import { StatsComponent, StatsResponse } from './StatsComponent';
import { mock, usesMoxios, renderWithSWR, wait } from './test.utils';
import { act } from '@testing-library/react';

usesMoxios();

test('render', async () => {
  const { container } = renderWithSWR(<StatsComponent />);

  await act(async () => {
    await mock<StatsResponse[]>('/api/stats', [
      { user: 'Mause', values: { episode: 1, movie: 1 } },
    ]);
    await wait();
  });

  expect(container).toMatchSnapshot();
});
