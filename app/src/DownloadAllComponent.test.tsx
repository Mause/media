import { renderWithSWR, mock, usesMoxios, wait } from "./test.utils";
import { DownloadAllComponent } from "./DownloadAllComponent";
import { MemoryRouter, Route } from "react-router-dom";
import React from "react";
import { ITorrent } from "./OptionsComponent";

usesMoxios();

test("DownloadAllComponent", async () => {
  const { container } = renderWithSWR(
    <MemoryRouter initialEntries={["/select/1/season/1/download_all"]}>
      <Route path="/select/:tmdb_id/season/:season/download_all">
        <DownloadAllComponent />
      </Route>
    </MemoryRouter>,
  );

  expect(container).toMatchSnapshot();

  const packs: ITorrent[] = [
    {
      source: "horriblesubs",
      category: "Movie",
      download: "magnet:....",
      episode_info: { seasonnum: 1, epnum: 1 },
      seeders: 5,
      title: "Hello World",
    },
  ];

  await mock("/api/select/1/season/1/download_all", {
    packs,
    incomplete: [],
    complete: [],
  });
  await wait();

  expect(container).toMatchSnapshot();
});
