import useSWR from 'swr';

import { DisplayError, RouteTitle, SearchBox } from './components';
import type { IndexResponse, Torrents } from './ParentComponent';
import { Movies, TVShows } from './render';

const CFG = {
  refreshInterval: 10000,
};
function IndexComponent() {
  const { data: state, isValidating: loadingState } = useSWR<IndexResponse>(
    'index',
    CFG,
  );
  const {
    data: torrents,
    isValidating: loadingTorrents,
    error,
  } = useSWR<Torrents, Error>('torrents', CFG);

  const loading = loadingState || loadingTorrents;

  const ostate = state || { series: [], movies: [] };

  return (
    <RouteTitle title="Media">
      <SearchBox />
      {error && <DisplayError error={error} />}
      <Movies torrents={torrents} movies={ostate.movies} loading={loading} />
      <TVShows torrents={torrents} series={ostate.series} loading={loading} />
    </RouteTitle>
  );
}

export { IndexComponent };
