import moxios from 'moxios';
import { swrConfig } from './streaming';
import { render } from '@testing-library/react';
import { ReactElement } from 'react';

export function wait() {
  return new Promise(resolve => moxios.wait(resolve));
}

export async function mock<T>(path: string, response: T) {
  await moxios.stubOnce('GET', new RegExp(path.replace(/\?/, '\\?')), {
    response,
  });
}

export function renderWithSWR(el: ReactElement) {
  return render(swrConfig(() => el)());
}

export function usesMoxios() {
  beforeEach(() => {
    moxios.install();
  });
  afterEach(() => {
    moxios.uninstall();
  });
}
