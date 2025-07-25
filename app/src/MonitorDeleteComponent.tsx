import { Navigate, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Axios from 'axios';

import { Loading, RouteTitle } from './components';

function useDelete(path: string) {
  const [done, setDone] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void Axios.delete(`/api/${path}`, {
      withCredentials: true,
      signal: controller.signal,
    }).then(() => setDone(true));
    return () => {
      controller.abort();
    };
  }, [path]);

  return done;
}

export function MonitorDeleteComponent() {
  const { id } = useParams<{ id: string }>();

  const done = useDelete(`monitor/${id}`);

  return (
    <RouteTitle title="Delete Monitor">
      {done ? <Navigate to="/monitor" /> : <Loading loading />}
    </RouteTitle>
  );
}
