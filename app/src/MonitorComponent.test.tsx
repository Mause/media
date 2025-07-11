import moxios from 'moxios';
import {
  unstable_HistoryRouter as HistoryRouter,
  MemoryRouter,
  Routes,
  Route,
} from 'react-router-dom';
import { createMemoryHistory } from '@remix-run/router';
import { act } from 'react';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as _ from 'lodash-es';

import type { Monitor } from './MonitorComponent';
import { MonitorComponent, MonitorAddComponent } from './MonitorComponent';
import {
  renderWithSWR,
  mock,
  wait,
  listenTo,
  expectLastRequestBody,
} from './test.utils';

describe('MonitorComponent', () => {
  it('view', async () => {
    const { container } = renderWithSWR(
      <MemoryRouter initialEntries={['/monitor']}>
        <Routes>
          <Route path="/" index element={<div>Home</div>} />
          <Route path="/monitor" Component={MonitorComponent} />
        </Routes>
      </MemoryRouter>,
    );

    const res: Monitor[] = [
      {
        id: 1,
        title: 'Hello World',
        tmdb_id: 5,
        type: 'MOVIE',
        status: false,
        added_by: {
          first_name: '',
          username: 'me',
        },
      },
    ];
    console.log('mocking');
    await mock('monitor', res);
    console.log('mocked');
    await wait();

    expect(container).toMatchSnapshot();
  });

  it('add', async () => {
    const hist = createMemoryHistory({
      initialEntries: ['/fake'],
      v5Compat: true,
    });
    const entries = listenTo(hist);

    renderWithSWR(
      <HistoryRouter history={hist}>
        <Routes>
          <Route
            path="/fake"
            element={<MonitorAddComponent tmdb_id={5} type={'MOVIE'} />}
          />
          <Route path="/monitor" element={<div>Monitor</div>} />
          <Route path="/" element={<div>Home</div>} />
        </Routes>
      </HistoryRouter>,
    );

    const events = userEvent.setup();

    await act(async () => {
      await events.click(await screen.findByText('Add to monitor'));
    });

    await wait();
    await act(async () => {
      expectLastRequestBody().toEqual({
        type: 'MOVIE',
        tmdb_id: 5,
      });
      await moxios.requests
        .mostRecent()
        .respondWith({ status: 200, response: {} });
    });
    await wait();

    expect(_.map(entries, 'pathname')).toEqual(['/monitor']);
  });
});
