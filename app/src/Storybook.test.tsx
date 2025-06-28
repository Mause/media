import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Storybook from './Storybook';
import { renderWithSWR } from './test.utils';

describe('Storybook', () => {
  it('renders without crashing', async () => {
    const user = userEvent.setup();
    const { container } = renderWithSWR(<Storybook />);

    const button = screen.getByTestId('context-menu-open');
    await user.click(button);

    expect(container).toMatchSnapshot();
  });
});
