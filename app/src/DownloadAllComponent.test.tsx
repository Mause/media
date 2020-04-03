import { renderWithSWR, mock, useMoxios, wait } from './test.utils';
import { DownloadAllComponent } from './DownloadAllComponent';
import { MemoryRouter, Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import React from 'react';
import { ITorrent } from './OptionsComponent';

useMoxios();

test('DownloadAllComponent', async () => {
  await act(async () => {
    const el = renderWithSWR(
      <MemoryRouter initialEntries={['/select/1/season/1/download_all']}>
        <Route path="/select/:tmdb_id/season/:season/download_all">
          <DownloadAllComponent />
        </Route>
      </MemoryRouter>,
    );

    expect(el.container).toMatchSnapshot();

    const packs: ITorrent[] = [
      {
        source: 'HORRIBLESUBS',
        category: 'Movie',
        download: 'magnet:....',
        episode_info: { seasonnum: '1', epnum: '1' },
        seeders: 5,
        title: 'Hello World',
      },
    ];

    await mock('/api/select/1/season/1/download_all', {
      packs,
      incomplete: [],
      complete: [],
    });
    await wait();

    expect(el.container).toMatchSnapshot();
  });
});
