import React from 'react';
import { render, act, wait } from '@testing-library/react';
import { OptionsComponent, ITorrent } from './OptionsComponent';
import { MemoryRouter, Route } from 'react-router-dom';
import { mock, useMoxios, renderWithSWR } from './test.utils';

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

    expect(el.container).toMatchSnapshot();

    const torrent: ITorrent = {
      title: 'title',
      seeders: 5,
      download: 'magnet:...',
      category: 'Movies/x264/1080',
    };

    sources[0]!.ls!({ data: JSON.stringify(torrent) });

    expect(el.container).toMatchSnapshot();
  });
});
