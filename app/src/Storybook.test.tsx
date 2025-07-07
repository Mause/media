import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { renderWithSWR } from './test.utils';
import { Storybook } from './Storybook';

describe('Storybook', () => {
  it('renders without crashing', async () => {
    const user = userEvent.setup();
    const { container } = renderWithSWR(
      <MemoryRouter>
        <Routes>
          <Route path="/" Component={Storybook} />
        </Routes>
      </MemoryRouter>,
    );

    const button = screen.getByTestId('context-menu-open');
    await user.click(button);

    expect(container).toMatchSnapshot();
  });
});
