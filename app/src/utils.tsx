import React from 'react';
import Axios from 'axios';
import { useState, useEffect } from 'react';
import qs from 'qs';
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
}) {
  return <MaterialLink component={Link} {...props} />;
}

export function subscribe(
  path: string,
  callback: (a: any) => void,
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

export function load<T>(path: string, params?: any): Promise<T> {
  return Axios.get<T>(`/api/${path}`, {
    params: qs.parse(params),
    withCredentials: true,
  }).then(t => t && t.data);
}

export function useLoad<T>(path: string, params: any = null) {
  const sparams = params ? qs.stringify(params) : null;
  const [data, setData] = useState<T>();
  useEffect(() => {
    load<T>(path, sparams).then(setData);
  }, [path, sparams]);
  return data;
}

export function usePost<T>(url: string, body: any): [boolean, T?] {
  const [done, setDone] = useState<[boolean, T?]>([false, undefined]);

  useEffect(() => {
    Axios.post<T>('/api/' + url, body, {
      withCredentials: true,
    }).then(res => setDone([true, res.data]));
  }, [url, body]);

  return done;
}
