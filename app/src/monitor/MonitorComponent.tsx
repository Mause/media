import useSWR from 'swr';
import { Navigate, useNavigate } from 'react-router-dom';
import MenuItem from '@mui/material/MenuItem';
import Axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircle, faTv, faTicketAlt } from '@fortawesome/free-solid-svg-icons';
import MaterialLink from '@mui/material/Link';
import Button from '@mui/material/Button';
import type { Auth0ContextInterface, User } from '@auth0/auth0-react';
import { useAuth0 } from '@auth0/auth0-react';
import useSWRMutation from 'swr/mutation';

import { ContextMenu, DisplayError, RouteTitle, Loading } from '../components';
import type { components, paths } from '../schema';
import { getPrefix, getToken } from '../utils';

type Monitor = components['schemas']['MonitorGet'];
type MonitorPost = components['schemas']['MonitorPost'];
type MediaType = components['schemas']['MonitorMediaType'];

export function MonitorComponent() {
  const auth = useAuth0();
  const { data } = useSWR<Monitor[]>('monitor');
  const navigate = useNavigate();

  const path = '/api/monitor/cron' as const;
  type MonitorCron = paths[typeof path]['post'];
  const { trigger: recheck, isMutating } = useSWRMutation(
    path,
    mutationFetcher<
      MonitorCron['requestBody'],
      MonitorCron['responses'][201]['content']['application/json']
    >(auth),
  );

  return (
    <RouteTitle title="Monitor">
      <h3>Monitored Media</h3>
      <Button
        loading={isMutating}
        variant="outlined"
        onClick={() => {
          void recheck();
        }}
      >
        Recheck
      </Button>
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
        <Loading loading />
      )}
    </RouteTitle>
  );
}

export function MonitorAddComponent({
  tmdb_id,
  type,
}: {
  tmdb_id: number;
  type: MediaType;
}) {
  const auth = useAuth0();
  const { data, error, trigger, isMutating } = useSWRMutation<
    Monitor,
    Error,
    string,
    MonitorPost
  >('/api/monitor', mutationFetcher<MonitorPost, Monitor>(auth));

  if (error) {
    return <DisplayError error={error} />;
  } else if (isMutating) {
    return <Loading loading />;
  } else if (data) {
    return <Navigate to="/monitor" />;
  } else {
    return (
      <MaterialLink href="#" onClick={() => void trigger({ tmdb_id, type })}>
        Add to monitor
      </MaterialLink>
    );
  }
}

function mutationFetcher<T, R>(
  auth: Auth0ContextInterface<User>,
): (
  key: string,
  options: Readonly<{
    arg: T;
  }>,
) => Promise<R> {
  return async function fetching(key: string, options: { arg: T }) {
    const res = await Axios.post(getPrefix() + key, options.arg, {
      headers: {
        Authorization: 'Bearer ' + (await getToken(auth)),
      },
    });
    return res.data as R;
  };
}

export type { Monitor };
