import Axios from 'axios';

export function subscribe(path: string, callback: (a: any) => void, end: (() => void) | null = null): void {
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
  return  Axios.get<T>(`/api/${path}`, { params, withCredentials: true }).then(t => t.data);
}
