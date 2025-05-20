import React from 'react';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithSWR } from './test.utils';
import Storybook from './Storybook';

describe('Storybook', () => {
  it('renders without crashing', async () => {
    const user = userEvent.setup();
    const { container } = renderWithSWR(<Storybook />);

    const button = screen.getByTestId('context-menu-open');
    await user.click(button);

    expect(container).toMatchSnapshot();
  });
});
