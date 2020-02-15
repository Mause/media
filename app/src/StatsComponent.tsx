import React from 'react';
import { useLoad } from './utils';
import ReactLoading from 'react-loading';

export type StatsResponse = {
  user: string;
  values: {
    movie: number;
    episode: number;
  };
};

export function StatsComponent() {
  const stats = useLoad<StatsResponse[]>('stats');

  if (!stats) return <ReactLoading type='balls' color='#000' />;

  return <div>
    {stats.map(({user, values}) => <div key={user}>
      <h3>{user}</h3>
      Movie: {values.movie || 0}<br />
      Episode: {values.episode || 0}<br />
    </div>)}
  </div>;
}
