import useSWR from 'swr';
import React, { useState, useEffect } from 'react';
import ReactLoading from 'react-loading';
import { Redirect, useParams, useHistory, useLocation } from 'react-router-dom';
import { usePost } from './utils';
import { ContextMenu, MenuItem } from 'react-contextmenu';
import { contextMenuTrigger } from './render';
import Axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircle, faTv, faTicketAlt } from '@fortawesome/free-solid-svg-icons';
import { DisplayError } from './IndexComponent';
import { components } from './schema';

type Monitor = components['schemas']['MonitorGet'];
type MediaType = components['schemas']['MonitorMediaType'];

export function MonitorComponent() {
  const { data } = useSWR<Monitor[]>('monitor');
  const history = useHistory();

  return (
    <div>
      <h3>Monitored Media</h3>
      {data ? (
        <ul>
          {data.map((m) => {
            const id = `monitor_${m.id}`;
            return (
              <li key={m.id}>
                <FontAwesomeIcon
                  icon={m.type === 'MOVIE' ? faTicketAlt : faTv}
                />
                &nbsp;
                {m.title}
                &nbsp;
                <FontAwesomeIcon
                  icon={faCircle}
                  className={m.status ? 'green' : 'red'}
                />
                &nbsp;
                {contextMenuTrigger(id)}
                <ContextMenu id={id}>
                  <MenuItem
                    onClick={() =>
                      history.push(
                        m.type === 'MOVIE'
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

  const { done, error } = usePost('monitor', {
    tmdb_id: Number(tmdb_id),
    type: state ? state.type : 'MOVIE',
  });

  if (error) {
    return <DisplayError error={error} />;
  }

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
