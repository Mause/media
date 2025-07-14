import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import axios from 'axios';
import moxios from 'moxios';

import { renderWithSWR } from './test.utils';
import { Storybook } from './Storybook';
import { server } from './msw';

describe('Storybook', () => {
  it('renders without crashing', async () => {
    moxios.uninstall(axios);
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
