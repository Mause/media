import { OpenPlex } from './OpenPlex';
import { describe, test } from 'vitest';
import { renderWithSWR } from '../test.utils';

describe('OpenPlex', () => {
  test('should render without crashing', () => {
    const el = renderWithSWR(
      <OpenPlex
        download={{
          tmdb_id: 12345,
        }}
        type="movie"
      />,
    );
    expect(el.container).toMatchSnapshot();
  });
});
