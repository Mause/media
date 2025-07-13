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
import axios from 'axios';
import { http, HttpResponse } from 'msw';

import { MonitorComponent, MonitorAddComponent } from './MonitorComponent';
import { renderWithSWR, listenTo, waitForRequests } from './test.utils';
import { server } from './msw';
import type { GetResponse } from './utils';
import type { paths } from './schema';

type MonitorResponse = GetResponse<paths['/api/monitor']>;

describe('MonitorComponent', () => {
  it('view', async () => {
    moxios.uninstall(axios);

    const { container } = renderWithSWR(
      <MemoryRouter initialEntries={['/monitor']}>
        <Routes>
          <Route path="/" index element={<div>Home</div>} />
          <Route path="/monitor" Component={MonitorComponent} />
        </Routes>
      </MemoryRouter>,
    );

    const res: MonitorResponse = [
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
    server.use(http.get('/api/monitor', () => HttpResponse.json(res)));
    await waitForRequests();

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

    server.use(
      http.post('/api/monitor', async ({ request }) => {
        expect(await request.json()).toEqual({
          type: 'MOVIE',
          tmdb_id: 5,
        });
        return HttpResponse.json({});
      }),
    );
    await waitForRequests();
    server.use(
      http.get('/api/monitor', () => {
        return HttpResponse.json([] satisfies MonitorResponse);
      }),
    );
    await waitForRequests();

    expect(_.map(entries, 'pathname')).toEqual(['/monitor']);
  });
});
