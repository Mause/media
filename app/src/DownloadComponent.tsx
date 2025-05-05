import React from "react";
import ReactLoading from "react-loading";
import { Redirect, useLocation } from "react-router-dom";
import { usePost } from "./utils";
import { DisplayError } from "./IndexComponent";
import { components } from "./schema";

export type DownloadCall = components["schemas"]["DownloadPost"];
export interface DownloadState {
  downloads: DownloadCall[];
}

export function DownloadComponent() {
  const { state } = useLocation<DownloadState>();

  const { done, error } = usePost(
    "download",
    state.downloads.map((item: DownloadCall) => ({
      ...item,
      tmdb_id: Number(item.tmdb_id),
    })),
  );

  if (error) {
    return <DisplayError error={error} />;
  }

  return done ? <Redirect to="/" /> : <ReactLoading color="#000000" />;
}
