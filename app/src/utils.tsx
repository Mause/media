import React, { ReactElement } from 'react';
import Axios from 'axios';
import { useState, useEffect } from 'react';
import MaterialLink from '@material-ui/core/Link';
import { Link } from 'react-router-dom';
import { LocationDescriptor } from 'history';
// import axiosRetry from '@vtex/axios-concurrent-retry';
import { TypographyTypeMap } from '@material-ui/core';
import moxios from 'moxios';
import { unstable_batchedUpdates } from 'react-dom';

// axiosRetry(Axios, { retries: 3 });

export function MLink<S>(props: {
  children: React.ReactNode;
  to: LocationDescriptor<S>;
  color?: TypographyTypeMap['props']['color'];
}): ReactElement {
  return <MaterialLink component={Link} {...props} />;
}

export function subscribe<T>(
  path: string,
  callback: (a: T) => void,
  error: (e: Error) => void,
  end: (() => void) | null = null,
): () => void {
  const es = new EventSource(path, {
    withCredentials: true,
  });
  es.onerror = (event: Event) => {
    error((event as unknown) as Error);
  };
  const internal_callback = ({ data }: { data: string }) => {
    if (!data) {
      if (end) {
        end();
      }
      es.close();
    } else {
      callback(JSON.parse(data));
    }
  };
  es.addEventListener('message', internal_callback);

  return () => {
    es.close();
    es.onerror = null;
    es.removeEventListener('message', internal_callback);
  };
}

export async function load<T>(path: string, params?: string): Promise<T> {
  const t = await Axios.get<T>(`/api/${path}`, {
    params,
    withCredentials: true,
  });
  return t && t.data;
}

export function usePost<T>(
  url: string,
  body: object,
): { done: boolean; data?: T; error?: Error } {
  const [done, setDone] = useState<boolean>(false);
  const [error, setError] = useState<Error>();
  const [data, setData] = useState<T>();

  useEffect(() => {
    Axios.post<T>('/api/' + url, body, {
      withCredentials: true,
    })
      .then(
        (res) => {
          unstable_batchedUpdates(() => {
            setDone(true);
            setData(res.data);
          });
        },
        (error) => {
          unstable_batchedUpdates(() => {
            setDone(true);
            setError(error);
          });
        },
      )
      .catch((error) => {
        unstable_batchedUpdates(() => {
          setDone(true);
          setError(error);
        });
      });
  }, [url, body]);

  return { done, error, data };
}

export function ExtMLink(props: { href: string; children: string }) {
  return (
    <MaterialLink href={props.href} target="_blank" rel="noopener noreferrer">
      {props.children}
    </MaterialLink>
  );
}

export function expectLastRequestBody() {
  return expect(JSON.parse(moxios.requests.mostRecent().config.data));
}
