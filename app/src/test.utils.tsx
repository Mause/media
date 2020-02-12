import moxios from "moxios";

export function wait() {
  return new Promise(resolve => moxios.wait(resolve));
}

export function mock<T>(path: string, response: T) {
  moxios.stubOnce('GET', new RegExp(path.replace(/\?/, '\\?')), {
    response,
  });
}

export function useMoxios() {
  beforeEach(() => {
    moxios.install();
  });
  afterEach(() => {
    moxios.uninstall();
  });
}
