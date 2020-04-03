import React from 'react';
import { act } from '@testing-library/react';
import { OptionsComponent, ITorrent } from './OptionsComponent';
import { MemoryRouter, Route } from 'react-router-dom';
import { mock, useMoxios, renderWithSWR, wait } from './test.utils';

useMoxios();

const sources: ES[] = [];
type CB = (event: { data: string }) => void;

class ES {
  public ls?: CB;
  constructor() {
    sources.push(this);
  }
  addEventListener(name: string, ls: CB) {
    this.ls = ls;
  }
  close() {}
}

Object.defineProperty(window, 'EventSource', { value: ES });

test('OptionsComponent', async () => {
  await act(async () => {
    const el = renderWithSWR(
      <MemoryRouter initialEntries={['/select/1/options']}>
        <Route path="/select/:tmdb_id/options">
          <OptionsComponent type="movie" />
        </Route>
      </MemoryRouter>,
    );
    await mock('movie/1', { title: 'Hello World' });
    await wait();

    expect(el.container).toMatchSnapshot();

    const torrent: ITorrent = {
      source: 'RARBG',
      title: 'title',
      seeders: 5,
      download: 'magnet:...',
      category: 'Movies/x264/1080',
    };

    const cb = sources[0]!.ls!;

    cb({ data: JSON.stringify(torrent) });

    expect(el.container).toMatchSnapshot();

    cb({ data: '' });

    expect(el.container).toMatchSnapshot();
  });
});
