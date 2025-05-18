import { act } from 'react';
import { screen } from '@testing-library/react';
import {
  OptionsComponent,
  ITorrent,
  TorrentProvider,
} from './OptionsComponent';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { mock, usesMoxios, renderWithSWR, wait } from './test.utils';
import { RecoilRoot } from 'recoil';
import _ from 'lodash';
import { vi } from 'vitest';
import { useAuth0 } from '@auth0/auth0-react';

vi.mock('@auth0/auth0-react', async (importOriginal) => {
  const original = await importOriginal();
  const useAuth0 = vi.fn();

  useAuth0.mockReturnValue({
    getAccessTokenSilently: vi.fn(),
  });

  return {
    ...original,
    useAuth0,
  };
});

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

function mockAuth0() {
  let lresolve: (value: unknown) => void;
  let promise = new Promise((resolve) => (lresolve = resolve));
  // @ts-expect-error
  useAuth0.mockReturnValue({
    getAccessTokenSilently: () => promise,
  });
  return lresolve;
}

function mockFetchStream(events: T[]) {
  const rs = new ReadableStream({
    start(controller) {
      for (const event of events) {
        controller.enqueue(
          Buffer.from('data: ' + JSON.stringify(event) + '\n'),
        );
      }
      controller.close();
    },
  });
  vi.spyOn(window, 'fetch').mockResolvedValue(new Response(rs));
}

describe('OptionsComponent', () => {
  it.skip('failure', async () => {
    let { container } = renderWithSWR(
      <MemoryRouter initialEntries={['/select/1/options']}>
        <Routes>
          <Route
            path="/select/:tmdb_id/options"
            element={
              <RecoilRoot>
                <OptionsComponent type="movie" />
              </RecoilRoot>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    await mock('movie/1', { title: 'Hello World' });
    await wait();

    expect(container).toMatchSnapshot();

    await act(async () => {
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
  it.skip('success', async () => {
    let { container } = renderWithSWR(
      <MemoryRouter initialEntries={['/select/1/options']}>
        <Routes>
          <Route
            path="/select/:tmdb_id/options"
            element={
              <RecoilRoot>
                <OptionsComponent type="movie" />
              </RecoilRoot>
            }
          />
        </Routes>
      </MemoryRouter>,
    );
    await act(async () => {
      mock('movie/1', { title: 'Hello World' });
    });

    expect(container).toMatchSnapshot();

    mockFetchStream([
      {
        source: 'rarbg',
        title: 'title',
        seeders: 5,
        download: 'magnet:...',
        category: 'x264/1080',
        episode_info: { seasonnum: 1, epnum: 1 },
      },
    ]);

    expect(container).toMatchSnapshot();

    await act(async () => {
      for (const source of sources) {
        source!.ls!({ data: '' });
      }
    });

    expect(container).toMatchSnapshot();
  });

  it('renders a single provider', async () => {
    const lresolve = mockAuth0();

    mockFetchStream([{}]);

    const { container } = renderWithSWR(
      <MemoryRouter initialEntries={['/select/1/options']}>
        <Routes>
          <Route
            path="/select/:tmdb_id/options"
            element={
              <RecoilRoot>
                <TorrentProvider baseUrl="/" params={{}} name="frogs" />
              </RecoilRoot>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(container).toMatchSnapshot();

    await act(() => {
      lresolve('token');
    });

    expect(container).toMatchSnapshot();
  });
});
