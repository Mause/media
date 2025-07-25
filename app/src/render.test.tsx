import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MockDate from 'mockdate';
import { http, HttpResponse } from 'msw';

import { Movies, TVShows, Progress, NextEpisodeAirs } from './render';
import { renderWithSWR, waitForRequests } from './test.utils';
import type {
  MovieResponse,
  Torrents,
  TorrentFile,
  SeriesResponse,
  EpisodeResponse,
} from './ParentComponent';
import { getMessage, shouldCollapse } from './utils';
import { server } from './msw';

beforeEach(() => MockDate.reset());

test('Movies', () => {
  const movies: MovieResponse[] = [
    {
      id: 1,
      download: {
        type: '',
        tmdb_id: 0,
        timestamp: '',
        title: 'Hello',
        added_by: {
          username: 'david',
          first_name: 'David',
        },
        id: 1,
        imdb_id: '',
        transmission_id: '',
      },
    },
  ];

  const { container } = render(<Movies movies={movies} loading={false} />);

  expect(container).toMatchSnapshot();
});

test('TVShows', () => {
  server.use(http.get('/api/tv/1/season/1', () => HttpResponse.json({})));
  server.use(http.get('/api/tv/1', () => HttpResponse.json({})));

  const series: SeriesResponse[] = [
    {
      tmdb_id: 1,
      imdb_id: '',
      title: 'Title',
      seasons: {
        1: [],
      },
    },
  ];
  const { container } = renderWithSWR(
    <MemoryRouter>
      <TVShows series={series} loading={false} />
    </MemoryRouter>,
  );

  expect(container).toMatchSnapshot();
});

describe('Progress', () => {
  it('simple', () => {
    function fn() {
      return <Progress item={item} torrents={torrents} />;
    }

    const item = { download: { transmission_id: 'GUID' } };
    const torrents: Torrents = {};
    const { container, rerender } = render(fn());

    expect(container).toMatchSnapshot();

    const torrent = (torrents['GUID'] = {
      eta: -1,
      percentDone: 1,
      files: [],
      hashString: '',
      id: 0,
    });
    rerender(fn());
    expect(container).toMatchSnapshot();

    torrent.percentDone = 0.5;
    torrent.eta = 360;
    rerender(fn());

    expect(container).toMatchSnapshot();
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

    const { container, rerender } = render(fn());
    expect(container).toMatchSnapshot();

    const torrent = (torrents['GUID'] = {
      id: 0,
      hashString: '',
      eta: -1,
      files: [] as TorrentFile[],
      percentDone: 0.5,
    });
    rerender(fn());
    expect(container).toMatchSnapshot();

    torrent.files.push({
      name: 'Title.S01E01.mkv',
      bytesCompleted: 3,
      length: 4,
    });
    rerender(fn());
    expect(container).toMatchSnapshot();
  });
});

describe('NextEpisodeAirs', () => {
  it('works', async () => {
    MockDate.set('2020-04-20');
    const tmdb_id = 10000;
    const season = '1';

    server.use(
      http.get(`/api/tv/${tmdb_id}/season/${season}`, () =>
        HttpResponse.json({
          episodes: [
            { name: 'EP2', air_date: '2020-04-24', episode_number: 2 },
          ],
        }),
      ),
    );

    const { container } = renderWithSWR(
      <MemoryRouter>
        <NextEpisodeAirs
          season={season}
          tmdb_id={tmdb_id}
          season_episodes={[{ episode: 1 }]}
        />
        ,
      </MemoryRouter>,
    );

    await waitForRequests();

    expect(container).toMatchSnapshot();
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
    imdb_id: null,
    title: '',
  };
  const episode: EpisodeResponse = {
    download: {
      id: 1,
      title: '',
      imdb_id: '',
      transmission_id: '',
      timestamp: '2022-01-01',
      tmdb_id: 0,
      type: '',
      added_by: {
        username: 'david',
        first_name: 'David',
      },
    },
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

describe('getMessage', () => {
  beforeEach(() => {
    MockDate.set('2020-01-03');
  });
  it('2020-01-01', () => {
    expect(getMessage('2020-01-01')).toBe('aired on 01/01/2020');
  });
  it('2020-01-02', () => {
    expect(getMessage('2020-01-02')).toBe('aired yesterday');
  });
  it('2020-01-03', () => {
    expect(getMessage('2020-01-03')).toBe('airs today');
  });
  it('2020-01-04', () => {
    expect(getMessage('2020-01-04')).toBe('airs tomorrow');
  });
  it('2020-01-05', () => {
    expect(getMessage('2020-01-05')).toBe('airs on 05/01/2020');
  });
});
