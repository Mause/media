import useSWR from 'swr';
import React from 'react';
import ReactLoading from 'react-loading';

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
