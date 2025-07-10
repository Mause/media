import { act } from 'react';
import { screen } from '@testing-library/react';
import { MemoryRouter, Route } from 'react-router-dom';
import * as _ from 'lodash-es';

import type { ITorrent } from './OptionsComponent';
import { MovieOptionsComponent } from './MovieOptionsComponent';
import { mock, renderWithSWR, wait } from './test.utils';

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
  removeEventListener() {}
  close() {
    _.remove(sources, this);
  }
}

Object.defineProperty(window, 'EventSource', { value: ES });

describe('OptionsComponent', () => {
  it.skip('failure', async () => {
    const { container } = renderWithSWR(
      <MemoryRouter initialEntries={['/select/1/options']}>
        <Route path="/select/:tmdb_id/options">
          <MovieOptionsComponent />
        </Route>
      </MemoryRouter>,
    );

    await mock('movie/1', { title: 'Hello World' });
    await wait();

    expect(container).toMatchSnapshot();

    act(() => {
      for (const source of sources) {
        source.onerror!(new Event('message'));
      }
    });

    expect(
      (await screen.findAllByTestId('errorMessage')).map((t) => t.textContent),
    ).toEqual(
      expect.arrayContaining([
        'Error occured whilst loading options from rarbg: [object Event]',
        'Error occured whilst loading options from horriblesubs: [object Event]',
        'Error occured whilst loading options from kickass: [object Event]',
      ]),
    );

    expect(container).toMatchSnapshot();
  });
  it.skip('success', () => {
    const { container } = renderWithSWR(
      <MemoryRouter initialEntries={['/select/1/options']}>
        <Route path="/select/:tmdb_id/options">
          <MovieOptionsComponent />
        </Route>
      </MemoryRouter>,
    );
    act(() => {
      void mock('movie/1', { title: 'Hello World' });
    });

    expect(container).toMatchSnapshot();

    const torrent: ITorrent = {
      source: 'rarbg',
      title: 'title',
      seeders: 5,
      download: 'magnet:...',
      category: 'x264/1080',
      episode_info: { seasonnum: 1, epnum: 1 },
    };

    expect(sources).toHaveLength(3);

    let i = 0;
    const source_names = ['RARBG', 'HORRIBLESUBS', 'KICKASS'];
    act(() => {
      for (const source of sources) {
        source.ls!({
          data: JSON.stringify({
            ...torrent,
            source: source_names[i],
            title: 'title ' + i++,
          }),
        });
      }
    });

    expect(container).toMatchSnapshot();

    act(() => {
      for (const source of sources) {
        source.ls!({ data: '' });
      }
    });

    expect(container).toMatchSnapshot();
  });
});
