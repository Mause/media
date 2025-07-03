import ReactLoading from 'react-loading';
import useSWR from 'swr';

import { RouteTitle } from './RouteTitle';

export type StatsResponse = {
  user: string;
  values: {
    movie: number;
    episode: number;
  };
};

export function StatsComponent() {
  const { data: stats } = useSWR<StatsResponse[]>('stats');

  if (!stats) return <ReactLoading type="balls" color="#000" />;

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
