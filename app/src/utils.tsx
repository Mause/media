import React, { ReactElement } from 'react';
import Axios from 'axios';
import { useState, useEffect } from 'react';
import MaterialLink from '@mui/material/Link';
import { Link } from 'react-router-dom';
import * as RRD from 'react-router-dom';
// import axiosRetry from '@vtex/axios-concurrent-retry';
import { TypographyTypeMap } from '@mui/material';
import moxios from 'moxios';
import { useAuth0 } from '@auth0/auth0-react';
import { FetchEventTarget } from './fetch_stream';

// axiosRetry(Axios, { retries: 3 });

export function MLink(
  props: {
    children: React.ReactNode;
    color?: TypographyTypeMap['props']['color'];
  } & Pick<Parameters<typeof Link>[0], 'to' | 'state'>,
): ReactElement {
  return <MaterialLink component={Link} {...props} underline="hover" />;
}

export function subscribe<T>(
  path: string,
  callback: (a: T) => void,
  error: (e: Error) => void,
  authorization: string,
  end: (() => void) | null = () => null,
): () => void {
  const es = FetchEventTarget(path, {
    headers: new Headers({
      Authorization: 'Bearer ' + authorization,
    }),
  });
  const onerror = (event: Event) => {
    error(event as unknown as Error);
  };
  es.addEventListener('abort', onerror);
  const internal_callback = (event: Event) => {
    callback((event as MessageEvent).data);
  };
  es.addEventListener('message', internal_callback);

  return () => {
    es.removeEventListener('close', end);
    es.removeEventListener('abort', onerror);
    es.removeEventListener('message', internal_callback);
  };
}

export function getPrefix() {
  const prefix = import.meta.env.REACT_APP_API_PREFIX;

  if (!prefix) {
    return '';
  } else if (prefix.includes('localhost')) {
    return `http://localhost:5000`;
  } else if (prefix) {
    return `https://${prefix}`;
  }
}

export async function load<T>(
  path: string,
  params?: string,
  headers?: any,
): Promise<T> {
  const t = await Axios.get<T>(`${getPrefix()}/api/${path}`, {
    params,
    withCredentials: true,
    headers,
  });
  return t && t.data;
}

interface Res<T> {
  data?: T;
  done: boolean;
  error?: Error;
}

export function usePost<T>(
  url: string,
  body: object,
): { done: boolean; data?: T; error?: Error } {
  const [result, setResult] = useState<Res<T>>({ done: false });
  const auth = useAuth0();

  useEffect(() => {
    const abortController = new AbortController();
    auth
      .getAccessTokenSilently()
      .then((token) =>
        Axios.post<T>('/api/' + url, body, {
          signal: abortController.signal,
          headers: {
            Authorization: 'Bearer ' + token,
          },
        }),
      )
      .then(
        (res) => {
          setResult({ done: true, data: res.data });
        },
        (error: unknown) => {
          setResult({ done: true, error: error as Error });
        },
      );

    return () => {
      abortController.abort();
    };
  }, [url, body, auth]);

  return result;
}

export function ExtMLink(props: { href: string; children: string }) {
  return (
    <MaterialLink
      href={props.href}
      target="_blank"
      rel="noopener noreferrer"
      underline="hover"
    >
      {props.children}
    </MaterialLink>
  );
}

export function expectLastRequestBody() {
  return expect(JSON.parse(moxios.requests.mostRecent().config.data));
}

export function useLocation<T>() {
  const location = RRD.useLocation();
  return { ...location, state: location.state as any as T };
}
