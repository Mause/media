import React from 'react';
import moxios from 'moxios';
import { swrConfig } from './streaming';
import { render } from '@testing-library/react';
import { ReactElement } from 'react';
import { Auth0Context, Auth0ContextInterface } from '@auth0/auth0-react';

export function wait() {
  return new Promise<void>((resolve) => moxios.wait(resolve));
}

export async function mock<T>(path: string, response: T) {
  await moxios.stubOnce('GET', new RegExp(path.replace(/\?/, '\\?')), {
    response,
  });
}

export function renderWithSWR(el: ReactElement) {
  const c = {
    isAuthenticated: true,
    getAccessTokenSilently() {
      return Promise.resolve('TOKEN');
    },
  } as Auth0ContextInterface;
  return render(
    <Auth0Context.Provider value={c}>
      {swrConfig(() => el)()}
    </Auth0Context.Provider>,
  );
}

export function usesMoxios() {
  beforeEach(() => {
    moxios.install();
  });
  afterEach(() => {
    moxios.uninstall();
  });
}
