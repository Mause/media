import { act, render } from "@testing-library/react";
import React from "react";
import { SearchComponent } from "./SearchComponent";
import { Route, MemoryRouter } from "react-router-dom";
import { mock, wait, useMoxios } from "./test.utils";

useMoxios();

test("SearchComponent", async () => {
  await act(async () => {
    const el = render(
      <MemoryRouter initialEntries={["/search?query=world"]}>
        <Route path="/search">
          <SearchComponent />
        </Route>
      </MemoryRouter>
    );

    const results: SearchResult[] = [
      {
        Type: "movie",
        imdbID: "10000",
        Year: 2019,
        title: "Hello"
      }
    ];
    await mock("/api/search", results);
    await wait();

    expect(el).toMatchSnapshot();
  });
});
