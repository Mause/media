import { renderWithSWR, wait, mock } from './test.utils';
import {
  ManualAddComponent,
  ManualAddComponentState,
} from './ManualAddComponent';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

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

  await mock('/api/tv/12345', {
    title: 'Test TV Show',
  });
  await wait();

  expect(container).toMatchSnapshot();
});
