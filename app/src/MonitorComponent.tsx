import useSWR from 'swr';
import React from 'react';
import ReactLoading from 'react-loading';
import { Redirect, useParams } from 'react-router-dom';
import { usePost } from './utils';

export function MonitorComponent() {
  const { data } = useSWR<{ title: string }[]>('monitor');

  return (
    <div>
      <h3>Monitored movies</h3>
      {data ? (
        <ul>
          {data.map(m => (
            <li>{m.title}</li>
          ))}
        </ul>
      ) : (
        <ReactLoading color="#000000" />
      )}
    </div>
  );
}

export function MonitorAddComponent() {
  const { tmdb_id } = useParams();

  const [done] = usePost('monitor', { tmdb_id });

  return done ? <Redirect to="/monitor" /> : <ReactLoading color="#000000" />;
}
