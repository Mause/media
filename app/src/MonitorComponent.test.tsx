import { useMoxios, renderWithSWR, mock, wait } from './test.utils';
import { act } from 'react-dom/test-utils';
import moxios from 'moxios';
import {
  MonitorComponent,
  Monitor,
  MediaType,
  MonitorAddComponent,
} from './MonitorComponent';
import React from 'react';
import { MemoryRouter, Route, Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import * as _ from 'lodash';
import { expectLastRequestBody } from './utils';

useMoxios();

describe('MonitorComponent', () => {
  it('view', async () => {
    await act(async () => {
      const el = renderWithSWR(
        <MemoryRouter>
          <MonitorComponent />
        </MemoryRouter>,
      );

      const res: Monitor[] = [
        {
          id: 1,
          title: 'Hello World',
          tmdb_id: '5',
          type: MediaType.MOVIE,
        },
      ];
      await mock('monitor', res);
      await wait();

      expect(el.container).toMatchSnapshot();
    });
  });

  it('add', async () => {
    await act(async () => {
      const hist = createMemoryHistory();
      hist.push({
        pathname: '/monitor/add/5',
        state: { type: MediaType.MOVIE },
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
