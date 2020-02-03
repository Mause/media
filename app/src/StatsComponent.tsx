import React from 'react';
import { useLoad } from './utils';
import _ from 'lodash';
import ReactLoading from 'react-loading';

export function StatsComponent() {
  const stats = useLoad<{
    [key: string]: {
      movie: number;
      episode: number;
    };
  }>('stats');

  if (!stats) return <ReactLoading type='balls' color='#000' />;

  return <div>
    {_.map(stats, (stat, username) => <div key={username}>
      <h3>{username}</h3>
      Movie: {stat.movie || 0}<br />
      Episode: {stat.episode || 0}<br />
    </div>)}
  </div>;
}
