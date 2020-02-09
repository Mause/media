import Axios from 'axios';
import { useState, useEffect } from 'react';
import qs from 'qs';

export const BASE = window.location.host.includes('localhost') ? 'http://localhost:5000' : '';

export function subscribe(path: string, callback: (a: any) => void, end: (() => void) | null = null): void {
  const es = new EventSource(BASE + path, {
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
  return Axios.get<T>(BASE + `/api/${path}`, { params: qs.parse(params), withCredentials: true }).then(t => t.data);
}

export function useLoad<T>(path: string, params: any = null) {
  const sparams = params ? qs.stringify(params) : null;
  const [data, setData] = useState<T>()
  useEffect(() => {
    load<T>(path, sparams).then(setData);
  }, [path, sparams]);
  return data;
}
