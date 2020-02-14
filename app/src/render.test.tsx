import { act, render } from "@testing-library/react";
import React from "react";
import { Movies, TvShows } from "./render";
import { Route, MemoryRouter } from "react-router-dom";
import { mock, wait, useMoxios } from "./test.utils";

useMoxios();

test("Movies", async () => {
  await act(async () => {
    const movies: SearchResult[] = [
      {
        id: 1,
        download: {
            title: "Hello"
            ,
            added_by: {
                first_name: 'David'
            }
        }
      }
    ];

    const el = render(<Movies movies={movies} />);

    expect(el).toMatchSnapshot();
  });
});
