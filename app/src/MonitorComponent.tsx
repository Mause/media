import useSWR from 'swr';
import React from 'react';
import ReactLoading from 'react-loading';

export function MonitorComponent() {
  const { data } = useSWR<{ id: number; tmdb_id: number }[]>('monitor');

  return (
    <div>
      <h3>Monitored movies</h3>
      {data ? (
        <ul>
          {data.map(m => (
            <li>
              {m.id} - {m.tmdb_id}
            </li>
          ))}
        </ul>
      ) : (
        <ReactLoading color="#000000" />
      )}
    </div>
  );
}
