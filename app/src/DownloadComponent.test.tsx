import { act, render } from '@testing-library/react';
import React from 'react';
import { DownloadComponent } from './streaming';
import { Route, Router } from 'react-router-dom';
import { mock, wait, useMoxios } from './test.utils';
import { createMemoryHistory } from 'history';

useMoxios();

test('DownloadComponent', async () => {
  await act(async () => {
    const history = createMemoryHistory();
    const state = {
      type: 'movie',
      imdb_id: 'tt10000',
      titles: 'Hello',
      magnet: '...',
    };
    history.push('/download', state);

    const el = render(
      <Router history={history}>
        <Route path="/download">
          <DownloadComponent />
        </Route>
      </Router>,
    );

    //await wait();
    expect(el).toMatchSnapshot();

    await mock('/download/movie?imdb_id=tt10000&magnet=...&titles=Hello', {});
    await wait();

    expect(el).toMatchSnapshot();
    expect(history.length).toBe(2);
  });
});
