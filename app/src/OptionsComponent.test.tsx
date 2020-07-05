import React from 'react';
import { act } from '@testing-library/react';
import { OptionsComponent, ITorrent } from './OptionsComponent';
import { MemoryRouter, Route } from 'react-router-dom';
import { mock, usesMoxios, renderWithSWR, wait } from './test.utils';
import _ from 'lodash';

usesMoxios();

const sources: ES[] = [];
type CB = (event: { data: string }) => void;

class ES {
  public onerror?: (event: Event) => void;
  public ls?: CB;
  constructor() {
    sources.push(this);
  }
  addEventListener(name: string, ls: CB) {
    this.ls = ls;
  }
  removeEventListener(name: string, ls: CB) {}
  close() {
    _.remove(sources, this);
  }
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
      category: 'x264/1080',
      episode_info: { seasonnum: '1', epnum: '1' },
    };

    expect(sources).toHaveLength(3);

    let i = 0;
    const source_names = ['RARBG', 'HORRIBLESUBS', 'KICKASS'];
    for (const source of sources) {
      source!.ls!({
        data: JSON.stringify({
          ...torrent,
          source: source_names[i],
          title: 'title ' + i++,
        }),
      });
    }

    expect(el.container).toMatchSnapshot();

    for (const source of sources) {
      source!.ls!({ data: '' });
    }

    expect(el.container).toMatchSnapshot();
  });
});
