import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse, http } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { server } from './msw';
import { Storybook } from './Storybook';
import { renderWithSWR } from './test.utils';

describe('Storybook', () => {
  it('renders without crashing', async () => {
    server.use(
      http.get('/api/tmdb/configuration', () =>
        HttpResponse.json({
          images: {
            poster_sizes: [],
          },
        }),
      ),
    );

    const user = userEvent.setup();
    const { container } = renderWithSWR(
      <MemoryRouter>
        <Routes>
          <Route path="/" Component={Storybook} />
        </Routes>
      </MemoryRouter>,
    );

    let button = screen.getByTestId('misc');
    await user.click(button);

    button = screen.getByTestId('context-menu-open');
    await user.click(button);

    expect(container).toMatchSnapshot();
  });
});
