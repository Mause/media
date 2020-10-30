import { act, render } from '@testing-library/react';
import React from 'react';
import {
  Movies,
  TVShows,
  Progress,
  shouldCollapse,
  NextEpisodeAirs,
} from './render';
import { MemoryRouter } from 'react-router-dom';
import { usesMoxios, renderWithSWR, mock, wait } from './test.utils';
import {
  MovieResponse,
  Torrents,
  TorrentFile,
  SeriesResponse,
  EpisodeResponse,
} from './streaming';
import MockDate from 'mockdate';

usesMoxios();
beforeEach(() => MockDate.reset());

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

describe('NextEpisodeAirs', () => {
  it('works', async () => {
    await act(async () => {
      MockDate.set('2020-04-20');
      const tmdb_id = '10000';
      const season = '1';
      const el = renderWithSWR(
        <MemoryRouter>
          <NextEpisodeAirs
            season={season}
            tmdb_id={tmdb_id}
            season_episodes={[{ episode: 1 }]}
          />
          ,
        </MemoryRouter>,
      );

      await mock(`tv/${tmdb_id}/season/${season}`, {
        episodes: [{ name: 'EP2', air_date: '2020-04-24', episode_number: 2 }],
      });
      await wait();

      expect(el.container).toMatchSnapshot();
    });
  });
});

describe('shouldCollapse', () => {
  const tv = {
    number_of_seasons: 1,
    seasons: [
      {
        season_number: 0,
        episode_count: 2,
      },
      {
        episode_count: 1,
        season_number: 1,
      },
    ],
    title: '',
  };
  const episode: EpisodeResponse = {
    download: { id: 1, title: '', imdb_id: '', transmission_id: '' },
    id: 1,
    episode: 1,
    season: 1,
    show_title: '',
  };

  it('true', () => {
    expect(shouldCollapse('1', tv, [episode])).toBe(true);
  });

  it('false', () => {
    expect(shouldCollapse('1', tv, [])).toBe(false);
  });

  it('true 2', () => {
    expect(shouldCollapse('1', tv, [episode, episode])).toBe(true);
  });
});
