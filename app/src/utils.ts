import { String } from 'typescript-string-operations';
import { useState, useEffect } from 'react';
import type { RawAxiosRequestHeaders } from 'axios';
import Axios from 'axios';
import * as RRD from 'react-router-dom';
// import axiosRetry from '@vtex/axios-concurrent-retry';
import type {
  Auth0ContextInterface,
  AuthenticationError,
} from '@auth0/auth0-react';
import { useAuth0 } from '@auth0/auth0-react';
import moment from 'moment';
import * as _ from 'lodash-es';

import { FetchEventTarget } from './fetch_stream';
import type { TV } from './SeasonSelectComponent';
import type { EpisodeResponse } from './streaming';

// axiosRetry(Axios, { retries: 3 });

export type GetResponse<T> = T extends {
  get: { responses: { '200': { content: { 'application/json': unknown } } } };
}
  ? T['get']['responses']['200']['content']['application/json']
  : never;

export function subscribe<T>(
  path: string,
  callback: (a: T) => void,
  error: (e: Error) => void,
  authorization: string,
  end: (() => void) | null = () => null,
): () => void {
  const es = FetchEventTarget(path, {
    headers: new Headers({
      Authorization: `Bearer ${authorization}`,
    }),
  });
  const onerror = (event: Event) => {
    error(event as unknown as Error);
  };
  es.addEventListener('abort', onerror);
  const internal_callback = (event: Event) => {
    callback((event as MessageEvent).data as T);
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
    return '';
  } else if (prefix) {
    return `https://${prefix}`;
  }
}

export async function load<T>(
  path: string,
  params?: object,
  headers?: RawAxiosRequestHeaders,
): Promise<T> {
  const url = `${getPrefix()}/api/${path}`;
  console.log('Loading', { url, params });
  const t = await Axios.get<T>(url, {
    params,
    withCredentials: true,
    headers,
  });
  return t?.data;
}

interface Res<T> {
  data?: T;
  done: boolean;
  error?: Error;
}

function isAuthenticationError(e: unknown): e is AuthenticationError {
  return typeof e === 'object' && e != null && 'error' in e;
}

export async function getToken(auth0: Auth0ContextInterface): Promise<string> {
  try {
    return await auth0.getAccessTokenSilently();
  } catch (e) {
    if (isAuthenticationError(e) && e.error === 'missing_refresh_token') {
      await auth0.loginWithRedirect({
        authorizationParams: {
          redirect_uri: window.location.toString(),
        },
      });
      return '';
    } else {
      throw e;
    }
  }
}

export function usePost<T>(
  url: string,
  body: object,
): { done: boolean; data?: T; error?: Error } {
  const [result, setResult] = useState<Res<T>>({ done: false });
  const auth = useAuth0();

  useEffect(() => {
    const abortController = new AbortController();
    getToken(auth)
      .then((token) =>
        Axios.post<T>(`/api/${url}`, body, {
          signal: abortController.signal,
          headers: {
            Authorization: `Bearer ${token}`,
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

export function useLocation<T>() {
  const location = RRD.useLocation();
  return { ...location, state: location.state as T };
}

export function getMarker(episode: {
  season?: number;
  episode?: number | null;
}) {
  if (episode.episode) {
    return String.format('S{0:00}E{1:00}', episode.season, episode.episode);
  } else {
    return String.format('S{0:00}', episode.season);
  }
}

export function getMessage(air_date: string) {
  const today = moment().startOf('day');
  const tomorrow = today.clone().add(1, 'day');
  const yesterday = today.clone().subtract(1, 'day');
  const dt = moment(air_date);
  const dts = dt.format('DD/MM/YYYY');

  let message;
  if (today.isSame(dt)) {
    message = 'airs today';
  } else if (dt.isSame(yesterday)) {
    message = 'aired yesterday';
  } else if (dt.isSame(tomorrow)) {
    message = 'airs tomorrow';
  } else if (dt.isAfter(today)) {
    message = `airs on ${dts}`;
  } else {
    message = `aired on ${dts}`;
  }
  return message;
}

export function shouldCollapse(
  i: string,
  data: TV | undefined,
  episodes: EpisodeResponse[],
): boolean {
  let collapse = false;
  if (data) {
    const i_i = +i;
    const seasonMeta = data.seasons.find((s) => s.season_number === i_i);
    if (seasonMeta) {
      const hasNext = true; // !!data.seasons[i_i + 1];

      const episodeNumbers = _.range(1, seasonMeta.episode_count + 1);
      const hasNumbers = _.map(episodes, 'episode');
      const hasAllEpisodes =
        _.difference(episodeNumbers, hasNumbers).length === 0;
      collapse = hasNext && hasAllEpisodes;
    }
  }
  return collapse;
}
