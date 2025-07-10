import { renderWithSWR, wait, mock } from './test.utils';
import { ManualAddComponent } from './ManualAddComponent';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { act } from 'react';

it('works', async () => {

  const { container } = renderWithSWR(
    <MemoryRouter
      initialEntries={[
        {
          pathname: '/',
          state: {
            tmdb_id: 12345,
            type: 'tv', // or 'movie'
            season: 1, // optional, for TV shows
          },
        },
      ]}
    >
      <Routes>
        <Route path="/" element={<ManualAddComponent />} />
      </Routes>
    </MemoryRouter>,
  );

  await mock('tv/12345', {
    id: 12345,
    name: 'Test TV Show',
    overview: 'This is a test TV show.',
    poster_path: '/test-poster.jpg',
  });
  console.log('Mocked TV show data for /api/tv/12345');
  await wait();

  expect(container).toMatchSnapshot();
});
