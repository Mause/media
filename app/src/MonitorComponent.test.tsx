import { renderWithSWR } from './test.utils';
import {
  MonitorComponent,
  MonitorAddComponent,
} from './MonitorComponent';
import { MemoryRouter, Route, Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';

describe('MonitorComponent', () => {
  it('view', async () => {
    const { container } = renderWithSWR(
      <MemoryRouter>
        <MonitorComponent />
      </MemoryRouter>,
    );

    expect(container).toMatchSnapshot();
  });

  it('add', async () => {
    const hist = createMemoryHistory();
    hist.push({
      pathname: '/monitor/add/5',
      state: { type: 'MOVIE' },
    });

    renderWithSWR(
      <Router history={hist}>
        <Route path="/monitor/add/:tmdb_id">
          <MonitorAddComponent />
        </Route>
      </Router>,
    );

    expect(_.map(hist.entries, 'pathname')).toEqual(['/', '/monitor']);
  });
});
