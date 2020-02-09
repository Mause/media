import { render, wait } from "@testing-library/react";
import React from "react";
import { act } from "react-dom/test-utils";
import { StatsComponent, StatsResponse } from "./StatsComponent";
import { mock, useMoxios } from "./test.utils";

useMoxios();

test('render', async () => {
  await act(async () => {
    const el = render(<StatsComponent />);

    mock<StatsResponse>('/api/stats', { Mause: { episode: 1, movie: 1 } });

    await wait();

    expect(el.findByText('Mause')).toBeTruthy();
    expect(el).toMatchSnapshot();
  })
})
