import React, { ReactElement } from 'react';
import Axios from 'axios';
import { useState, useEffect } from 'react';
import MaterialLink from '@material-ui/core/Link';
import { Link } from 'react-router-dom';
import { LocationDescriptor } from 'history';

import axiosRetry from '@vtex/axios-concurrent-retry';
import { TypographyTypeMap } from '@material-ui/core';

axiosRetry(Axios, { retries: 3 });

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
  end: (() => void) | null = null,
): void {
  const es = new EventSource(path, {
    withCredentials: true,
  });
  es.addEventListener('message', ({ data }) => {
    if (!data) {
      if (end) {
        end();
      }
      return es.close();
    }
    callback(JSON.parse(data));
  });
}

export async function load<T>(path: string, params?: string): Promise<T> {
  const t = await Axios.get<T>(`/api/${path}`, {
    params,
    withCredentials: true,
  });
  return t && t.data;
}

export function usePost<T>(url: string, body: object): [boolean, T?] {
  const [done, setDone] = useState<[boolean, T?]>([false, undefined]);

  useEffect(() => {
    Axios.post<T>('/api/' + url, body, {
      withCredentials: true,
    }).then(res => setDone([true, res.data]));
  }, [url, body]);

  return done;
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
