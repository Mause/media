import React from 'react';
import { render, act, wait } from '@testing-library/react';
import { OptionsComponent, ITorrent } from './OptionsComponent';
import { MemoryRouter, Route } from 'react-router-dom';

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
    const el = render(
      <MemoryRouter initialEntries={['/select/1/options']}>
        <Route path="/select/:tmdb_id/options">
          <OptionsComponent type="movie" />
        </Route>
      </MemoryRouter>,
    );
    expect(el.container).toMatchSnapshot();

    await wait();

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
