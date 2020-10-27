import React from 'react';
import { act, RenderResult } from '@testing-library/react';
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

describe('OptionsComponent', () => {
  it.skip('failure', async () => {
    let el: RenderResult;

    await act(async () => {
      el = renderWithSWR(
        <MemoryRouter initialEntries={['/select/1/options']}>
          <Route path="/select/:tmdb_id/options">
            <OptionsComponent type="movie" />
          </Route>
        </MemoryRouter>,
      );
      await mock('movie/1', { title: 'Hello World' });
      await wait();
    });

    console.assert(el);

    expect(el).toBeTruthy();

    expect(el.container).toMatchSnapshot();

    await act(async () => {
      for (const source of sources) {
        source.onerror!(new Event('message'));
      }
    });

    expect(
      (await el.findAllByTestId('errorMessage')).map((t) => t.textContent),
    ).toEqual(
      expect.arrayContaining([
        'Error occured whilst loading options from rarbg: [object Event]',
        'Error occured whilst loading options from horriblesubs: [object Event]',
        'Error occured whilst loading options from kickass: [object Event]',
      ]),
    );

    expect(el.container).toMatchSnapshot();
  });
  it.skip('success', async () => {
    let el;
    await act(async () => {
      el = renderWithSWR(
        <MemoryRouter initialEntries={['/select/1/options']}>
          <Route path="/select/:tmdb_id/options">
            <OptionsComponent type="movie" />
          </Route>
        </MemoryRouter>,
      );
      mock('movie/1', { title: 'Hello World' });
    });

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
    await act(async () => {
      for (const source of sources) {
        source!.ls!({
          data: JSON.stringify({
            ...torrent,
            source: source_names[i],
            title: 'title ' + i++,
          }),
        });
      }
    });

    expect(el.container).toMatchSnapshot();

    await act(async () => {
      for (const source of sources) {
        source!.ls!({ data: '' });
      }
    });

    expect(el.container).toMatchSnapshot();
  });
});
