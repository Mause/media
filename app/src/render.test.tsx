import { act, render } from '@testing-library/react';
import React from 'react';
import { Movies, TVShows, Progress } from './render';
import { MemoryRouter } from 'react-router-dom';
import { useMoxios, renderWithSWR } from './test.utils';
import {
  MovieResponse,
  Torrents,
  TorrentFile,
  SeriesResponse,
} from './streaming';

useMoxios();

test('Movies', () => {
  const movies: MovieResponse[] = [
    {
      id: 1,
      download: {
        title: 'Hello',
        added_by: {
          first_name: 'David',
        },
        id: 1,
        imdb_id: '',
        transmission_id: '',
      },
    },
  ];

  const el = render(<Movies movies={movies} loading={false} />);

  expect(el.container).toMatchSnapshot();
});

test('TVShows', async () => {
  await act(async () => {
    const series: SeriesResponse[] = [
      {
        tmdb_id: '1',
        imdb_id: '',
        title: 'Title',
        seasons: {
          1: [],
        },
      },
    ];
    const el = renderWithSWR(
      <MemoryRouter>
        <TVShows series={series} loading={false} />
      </MemoryRouter>,
    );

    expect(el.container).toMatchSnapshot();
  });
});

describe('Progress', () => {
  it('simple', () => {
    function fn() {
      return <Progress item={item} torrents={torrents} />;
    }

    const item = { download: { transmission_id: 'GUID' } };
    const torrents: Torrents = {};
    const el = render(fn());

    expect(el.container).toMatchSnapshot();

    const torrent = (torrents['GUID'] = {
      eta: -1,
      percentDone: 1,
      files: [],
    });
    el.rerender(fn());
    expect(el.container).toMatchSnapshot();

    torrent.percentDone = 0.5;
    torrent.eta = 360;
    el.rerender(fn());

    expect(el.container).toMatchSnapshot();
  });

  it('complex', () => {
    function fn() {
      return <Progress item={item} torrents={torrents} />;
    }
    const item = {
      download: { transmission_id: 'GUID.1' },
      season: 1,
      episode: 1,
    };
    const torrents: Torrents = {};

    const el = render(fn());
    expect(el.container).toMatchSnapshot();

    const torrent = (torrents['GUID'] = {
      eta: -1,
      files: [] as TorrentFile[],
      percentDone: 0.5,
    });
    el.rerender(fn());
    expect(el.container).toMatchSnapshot();

    torrent.files.push({
      name: 'Title.S01E01.mkv',
      bytesCompleted: 3,
      length: 4,
    });
    el.rerender(fn());
    expect(el.container).toMatchSnapshot();
  });
});
