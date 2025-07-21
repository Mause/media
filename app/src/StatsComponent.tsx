import useSWR from 'swr';

import { Loading, RouteTitle } from './components';

export type StatsResponse = {
  user: string;
  values: {
    movie: number;
    episode: number;
  };
};

export function StatsComponent() {
  const { data: stats } = useSWR<StatsResponse[]>('stats');

  if (!stats) return <Loading loading />;

  return (
    <RouteTitle title="Stats">
      {stats.map(({ user, values }) => (
        <div key={user}>
          <h3>{user}</h3>
          Movie: {values.movie || 0}
          <br />
          Episode: {values.episode || 0}
          <br />
        </div>
      ))}
    </RouteTitle>
  );
}
