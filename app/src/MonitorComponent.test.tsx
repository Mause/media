import { usesMoxios, renderWithSWR, mock, wait } from './test.utils';
import { act } from 'react-dom/test-utils';
import moxios from 'moxios';
import {
  MonitorComponent,
  Monitor,
  MonitorAddComponent,
} from './MonitorComponent';
import React from 'react';
import { MemoryRouter, Route, Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import * as _ from 'lodash';
import { expectLastRequestBody } from './utils';

usesMoxios();

describe('MonitorComponent', () => {
  it('view', async () => {
    await act(async () => {
      const { container } = renderWithSWR(
        <MemoryRouter>
          <MonitorComponent />
        </MemoryRouter>,
      );

      const res: Monitor[] = [
        {
          id: 1,
          title: 'Hello World',
          tmdb_id: 5,
          type: 'MOVIE',
          added_by: 'me',
        },
      ];
      await mock('monitor', res);
      await wait();

      expect(container).toMatchSnapshot();
    });
  });

  it('add', async () => {
    await act(async () => {
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

      await wait();
      expectLastRequestBody().toEqual({
        type: 'MOVIE',
        tmdb_id: 5,
      });
      await moxios.requests
        .mostRecent()
        .respondWith({ status: 200, response: {} });

      expect(_.map(hist.entries, 'pathname')).toEqual(['/', '/monitor']);
    });
  });
});
