import React from 'react';
import { StatsComponent, StatsResponse } from './StatsComponent';
import { mock, usesMoxios, renderWithSWR, wait } from './test.utils';
import { act } from '@testing-library/react';

usesMoxios();

test('render', async () => {
  await act(async () => {
    const el = renderWithSWR(<StatsComponent />);

    await mock<StatsResponse[]>('/api/stats', [
      { user: 'Mause', values: { episode: 1, movie: 1 } },
    ]);
    await wait();

    expect(el.container).toMatchSnapshot();
  });
});
