import useSWR from 'swr';
import React, { useState, useEffect } from 'react';
import ReactLoading from 'react-loading';
import { Redirect, useParams, useHistory } from 'react-router-dom';
import { usePost } from './utils';
import { ContextMenu, MenuItem } from 'react-contextmenu';
import { contextMenuTrigger } from './render';
import Axios from 'axios';

export function MonitorComponent() {
  const { data } = useSWR<{ title: string; id: number; tmdb_id: string }[]>(
    'monitor',
  );
  const history = useHistory();

  return (
    <div>
      <h3>Monitored movies</h3>
      {data ? (
        <ul>
          {data.map(m => {
            let id = `monitor_${m.id}`;
            return (
              <li key={m.id}>
                {m.title}&nbsp;
                {contextMenuTrigger(id)}
                <ContextMenu id={id}>
                  <MenuItem
                    onClick={() => history.push(`/select/${m.tmdb_id}/options`)}
                  >
                    Search
                  </MenuItem>
                  <MenuItem
                    onClick={() => history.push(`/monitor/delete/${m.id}`)}
                  >
                    Delete
                  </MenuItem>
                </ContextMenu>
              </li>
            );
          })}
        </ul>
      ) : (
        <ReactLoading color="#000000" />
      )}
    </div>
  );
}

export function MonitorAddComponent() {
  const { tmdb_id } = useParams();

  const [done] = usePost('monitor', { tmdb_id, type: 'MOVIE' });

  return done ? <Redirect to="/monitor" /> : <ReactLoading color="#000000" />;
}

function useDelete(path: string) {
  const [done, setDone] = useState(false);

  useEffect(() => {
    Axios.delete(`/api/${path}`, { withCredentials: true }).then(() =>
      setDone(true),
    );
  }, [path]);

  return done;
}

export function MonitorDeleteComponent() {
  const { id } = useParams();

  const done = useDelete(`monitor/${id}`);

  return done ? <Redirect to="/monitor" /> : <ReactLoading color="#000000" />;
}
