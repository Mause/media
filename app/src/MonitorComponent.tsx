import useSWR from 'swr';
import React from 'react';
import ReactLoading from 'react-loading';
import { Redirect, useParams, useHistory } from 'react-router-dom';
import { usePost } from './utils';
import { ContextMenu, MenuItem } from 'react-contextmenu';
import { contextMenuTrigger } from './render';

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
              <li>
                {m.title}&nbsp;
                {contextMenuTrigger(id)}
                <ContextMenu id={id}>
                  <MenuItem
                    onClick={() => history.push(`/select/${m.tmdb_id}/options`)}
                  >
                    Search
                  </MenuItem>
                  <MenuItem
                    onClick={() => history.push(`/monitor/delete/${t.id}`)}
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

  const [done] = usePost('monitor', { tmdb_id });

  return done ? <Redirect to="/monitor" /> : <ReactLoading color="#000000" />;
}
