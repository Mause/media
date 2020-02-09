import { render, act } from "@testing-library/react";
import { SeasonSelectComponent, Season, EpisodeSelectComponent, TV } from "./SeasonSelectComponent";
import React from "react";
import { MemoryRouter, Route } from "react-router-dom";
import moxios from 'moxios';

beforeEach(() => {
  moxios.install();
});
afterEach(() => {
  moxios.uninstall();
})

function wait() {
  return new Promise(resolve => moxios.wait(resolve));
}

test('SeasonSelectComponent  render', async () => {
  await act(async () => {
    let el = render(<MemoryRouter initialEntries={['/select/1/season']}>
      <Route path="/select/:tmdb_id/season"><SeasonSelectComponent /></Route>
    </MemoryRouter>);

    moxios.stubOnce('GET', /\/api\/tv\/1/, {
      response: { title: 'Hello', }
    });
    await wait();

    expect(el.getByTestId('title').textContent).toEqual("Hello");
  });
});

test('EpisodeSelectComponent render', async () => {
  await act(async () => {
    let el = render(<MemoryRouter initialEntries={['/select/1/season/1']}>
      <Route path="/select/:tmdb_id/season/:season"><EpisodeSelectComponent /></Route>
    </MemoryRouter>);

    const response: Season = {
      episodes: [{
        episode_number: 1,
        id: '1',
        name: 'Episode 1',
      }],
    };
    moxios.stubOnce('GET', /\/api\/tv\/1\/season\/1/, { response, });
    await wait();

    expect(el.getByTestId('title').textContent).toEqual("Season 1");
  });
});
