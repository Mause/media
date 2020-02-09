import moxios from "moxios";
import { act } from "react-dom/test-utils";
import { render, wait } from "@testing-library/react";
import { StatsComponent, StatsResponse } from "./StatsComponent";
import React from "react";
import { mock } from "./SeasonSelectComponent.test";
import { EpisodeSelectComponent } from "./SeasonSelectComponent";


beforeEach(() => {
  moxios.install();
});
afterEach(() => {
  moxios.uninstall();
});


test('render', async () => {
  await act(async () => {
    const el = render(<StatsComponent />);

    mock<StatsResponse>('/api/stats', { Mause: { episode: 1, movie: 1 } });

    await wait();

    expect(el.findByText('Mause')).toBeTruthy();
    expect(el).toMatchSnapshot();
  })
})
