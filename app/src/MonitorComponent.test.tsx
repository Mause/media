import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse, http } from 'msw';
import { act } from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { MonitorAddComponent, MonitorComponent } from './MonitorComponent';
import { server } from './msw';
import type { paths } from './schema';
import { renderWithSWR, waitForRequests } from './test.utils';
import type { GetResponse } from './utils';

type MonitorResponse = GetResponse<paths['/api/monitor']>;

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
    const { container } = renderWithSWR(
      <MemoryRouter initialEntries={['/fake']}>
        <Routes>
          <Route
            path="/fake"
            element={<MonitorAddComponent tmdb_id={5} type={'MOVIE'} />}
          />
          <Route path="/monitor" element={<div>Monitor</div>} />
        </Routes>
      </MemoryRouter>,
    );

    const events = userEvent.setup();

    server.use(
      http.post('/api/monitor', async ({ request }) => {
        expect(await request.json()).toEqual({
          type: 'MOVIE',
          tmdb_id: 5,
        });
        return HttpResponse.json({});
      }),
    );
    server.use(
      http.get('/api/monitor', () => {
        return HttpResponse.json([] satisfies MonitorResponse);
      }),
    );

    await act(async () => {
      await events.click(await screen.findByText('Add to monitor'));
    });

    expect(container).toMatchSnapshot();
  });
});
