import useSWR from 'swr';
import React, { useState, useEffect } from 'react';
import ReactLoading from 'react-loading';
import { Redirect, useParams, useHistory, useLocation } from 'react-router-dom';
import { usePost } from './utils';
import { ContextMenu, MenuItem } from 'react-contextmenu';
import { contextMenuTrigger } from './render';
import Axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTv, faTicketAlt } from '@fortawesome/free-solid-svg-icons';

export enum MediaType {
  'MOVIE' = 'MOVIE',
  'TV' = 'TV',
}

export interface Monitor {
  title: string;
  id: number;
  type: MediaType;
  tmdb_id: string;
}

export function MonitorComponent() {
  const { data } = useSWR<Monitor[]>('monitor');
  const history = useHistory();

  return (
    <div>
      <h3>Monitored Media</h3>
      {data ? (
        <ul>
          {data.map(m => {
            let id = `monitor_${m.id}`;
            return (
              <li key={m.id}>
                <FontAwesomeIcon
                  icon={m.type === MediaType.MOVIE ? faTicketAlt : faTv}
                />
                &nbsp;
                {m.title}
                &nbsp;
                {contextMenuTrigger(id)}
                <ContextMenu id={id}>
                  <MenuItem
                    onClick={() =>
                      history.push(
                        m.type === MediaType.MOVIE
                          ? `/select/${m.tmdb_id}/options`
                          : `/select/${m.tmdb_id}/season`,
                      )
                    }
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
  const { state } = useLocation<{ type: MediaType }>();

  const [done] = usePost('monitor', {
    tmdb_id: Number(tmdb_id),
    type: state ? state.type : MediaType.MOVIE,
  });

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
