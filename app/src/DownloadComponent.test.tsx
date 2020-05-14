import { act, RenderResult } from '@testing-library/react';
import React from 'react';
import { DownloadComponent, DownloadState } from './DownloadComponent';
import { Route, Router } from 'react-router-dom';
import { wait, usesMoxios, renderWithSWR } from './test.utils';
import { createMemoryHistory } from 'history';
import moxios from 'moxios';
import { expectLastRequestBody } from './utils';

usesMoxios();

describe('DownloadComponent', () => {
  it('success', async () => {
    await act(async () => {
      const history = createMemoryHistory();
      const state: DownloadState = {
        downloads: [
          {
            tmdb_id: '10000',
            magnet: '...',
          },
        ],
      };
      history.push('/download', state);

      const el = renderWithSWR(
        <Router history={history}>
          <Route path="/download">
            <DownloadComponent />
          </Route>
        </Router>,
      );

      expect(el.container).toMatchSnapshot();

      await moxios.stubOnce('POST', /\/api\/download/, {});
      expectLastRequestBody().toEqual([{ magnet: '...', tmdb_id: 10000 }]);
      await wait();

      expect(el.container).toMatchSnapshot();
      expect(history.length).toBe(2);
    });
  });
  it('failure', async () => {
    const history = createMemoryHistory();
    const state: DownloadState = {
      downloads: [
        {
          tmdb_id: '10000',
          magnet: '...',
        },
      ],
    };
    history.push('/download', state);

    let el: RenderResult;
    await act(async () => {
      el = renderWithSWR(
        <Router history={history}>
          <Route path="/download">
            <DownloadComponent />
          </Route>
        </Router>,
      );

      await moxios.stubFailure('POST', /\/api\/download/, {
        status: 500,
        response: { body: {}, message: 'an error has occured' },
      });
    });

    expect(await el!.findByTestId('errorMessage')).toHaveTextContent(
      'an error has occured',
    );
  });
});
