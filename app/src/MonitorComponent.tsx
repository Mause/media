import useSWR from 'swr';
import { useState, useEffect } from 'react';
import ReactLoading from 'react-loading';
import { Navigate, useNavigate, useParams } from 'react-router-dom';
import MenuItem from '@mui/material/MenuItem';
import ContextMenu from './ContextMenu';
import { usePost, useLocation } from './utils';
import Axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircle, faTv, faTicketAlt } from '@fortawesome/free-solid-svg-icons';
import { DisplayError } from './IndexComponent';
import { components } from './schema';

type Monitor = components['schemas']['MonitorGet'];
type MediaType = components['schemas']['MonitorMediaType'];

export function MonitorComponent() {
  const { data } = useSWR<Monitor[]>('monitor');
  const navigate = useNavigate();

  return (
    <div>
      <h3>Monitored Media</h3>
      {data ? (
        <ul>
          {data.map((m) => {
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
                <ContextMenu>
                  <MenuItem
                    onClick={() =>
                      void navigate(
                        m.type === 'MOVIE'
                          ? `/select/${m.tmdb_id}/options`
                          : `/select/${m.tmdb_id}/season`,
                      )
                    }
                  >
                    Search
                  </MenuItem>
                  <MenuItem
                    onClick={() => void navigate(`/monitor/delete/${m.id}`)}
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
  const { tmdb_id } = useParams<{ tmdb_id: string }>();
  const { state } = useLocation<{ type: MediaType }>();

  const { done, error } = usePost('monitor', {
    tmdb_id: Number(tmdb_id),
    type: state ? state.type : 'MOVIE',
  });

  if (error) {
    return <DisplayError error={error} />;
  }

  return done ? <Navigate to="/monitor" /> : <ReactLoading color="#000000" />;
}

function useDelete(path: string) {
  const [done, setDone] = useState(false);

  useEffect(() => {
    void Axios.delete(`/api/${path}`, { withCredentials: true }).then(() =>
      setDone(true),
    );
  }, [path]);

  return done;
}

export function MonitorDeleteComponent() {
  const { id } = useParams<{ id: string }>();

  const done = useDelete(`monitor/${id}`);

  return done ? <Navigate to="/monitor" /> : <ReactLoading color="#000000" />;
}

export type { Monitor };
