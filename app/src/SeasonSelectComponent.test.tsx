import { act, render } from "@testing-library/react";
import React from "react";
import { MemoryRouter, Route } from "react-router-dom";
import { EpisodeSelectComponent, Season, SeasonSelectComponent, TV } from "./SeasonSelectComponent";
import { mock, useMoxios, wait } from "./utils.test";

useMoxios();

test('SeasonSelectComponent  render', async () => {
  await act(async () => {
    let el = render(<MemoryRouter initialEntries={['/select/1/season']}>
      <Route path="/select/:tmdb_id/season"><SeasonSelectComponent /></Route>
    </MemoryRouter>);

    mock<TV>('/api/tv/1', {
      title: 'Hello',
      number_of_seasons: 1,
      seasons: [{ episode_count: 1 }]
    });
    await wait();

    expect(el.getByTestId('title').textContent).toEqual("Hello");
    expect(el).toMatchSnapshot();
  });
});

test('EpisodeSelectComponent render', async () => {
  await act(async () => {
    let el = render(<MemoryRouter initialEntries={['/select/1/season/1']}>
      <Route path="/select/:tmdb_id/season/:season"><EpisodeSelectComponent /></Route>
    </MemoryRouter>);

    mock<Season>('/api/tv/1/season/1', {
      episodes: [{
        episode_number: 1,
        id: '1',
        name: 'Episode 1',
      }],
    });
    await wait();

    expect(el.getByTestId('title').textContent).toEqual("Season 1");
  });
});
