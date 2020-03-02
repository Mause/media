import React from 'react';
import { render } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  const el = render(<App />);
  expect(el.container).toMatchSnapshot();
});
