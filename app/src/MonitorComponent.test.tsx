import { usesMoxios, renderWithSWR, mock, wait, listenTo } from './test.utils';
import moxios from 'moxios';
import {
  MonitorComponent,
  Monitor,
  MonitorAddComponent,
} from './MonitorComponent';
import {
  unstable_HistoryRouter as HistoryRouter,
  MemoryRouter,
  Routes,
  Route,
} from 'react-router-dom';
import * as _ from 'lodash';
import { expectLastRequestBody } from './utils';
import { createMemoryHistory } from '@remix-run/router';
import { act } from 'react';

usesMoxios();

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
      initialEntries: [
        {
          pathname: '/monitor/add/5',
          state: { type: 'MOVIE' },
        },
      ],
      v5Compat: true,
    });
    const entries = listenTo(hist);

    renderWithSWR(
      <HistoryRouter history={hist}>
        <Routes>
          <Route path="/monitor/add/:tmdb_id" Component={MonitorAddComponent} />
          <Route path="/monitor" element={<div>Monitor</div>} />
          <Route path="/" element={<div>Home</div>} />
        </Routes>
      </HistoryRouter>,
    );

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
