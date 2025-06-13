import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import axios from 'axios';

export default function AxiosErrorCatcher(props: { children: ReactNode }) {
  const [error, setError] = useState<Error>();

  useEffect(() => {
    const reqId = axios.interceptors.request.use((req) => {
      setError(undefined);
      return req;
    });
    const resId = axios.interceptors.response.use((req) => req, setError);

    return () => {
      axios.interceptors.request.eject(reqId);
      axios.interceptors.response.eject(resId);
    };
  }, []);

  if (error) throw error;

  return props.children;
}
