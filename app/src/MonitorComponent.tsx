import useSWR from 'swr';
import React from 'react';
import { useState, useEffect } from 'react';
import ReactLoading from 'react-loading';
import { Redirect, useParams } from 'react-router-dom';
import Axios from 'axios';
import { BASE } from './utils';

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
  const [done, setDone] = useState(false);
  const { tmdb_id } = useParams();

  useEffect(() => {
    Axios.post(
      BASE + '/api/monitor',
      { tmdb_id },
      { withCredentials: true },
    ).then(() => setDone(true));
  }, [tmdb_id]);

  return done ? <Redirect to="/monitor" /> : <ReactLoading color="#000000" />;
}
