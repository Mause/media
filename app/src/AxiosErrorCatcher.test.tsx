import { render } from '@testing-library/react';
import React, { useEffect, useState } from 'react';
import AxiosErrorCatcher from './AxiosErrorCatcher';
import { wait, usesMoxios } from './test.utils';
import moxios from 'moxios';
import axios from 'axios';
import { ErrorBoundary } from 'react-error-boundary';

usesMoxios();

/*
beforeEach(() => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  console.error.mockRestore();
});
*/

function Fake() {
  const [fire, setFire] = useState(false);
  useEffect(() => {
    if (fire) void axios.get('/');
    else setFire(true);
  }, [fire]);
  return <div>Thing</div>;
}

test('AxiosErrorCatcher', async () => {
  let lerror: unknown;
  const { container } = render(
    <ErrorBoundary
      fallback={<div>error</div>}
      onError={(error) => (lerror = error)}
    >
      <AxiosErrorCatcher>
        <Fake />
      </AxiosErrorCatcher>
    </ErrorBoundary>,
  );

  expect(container).toMatchSnapshot();

  await moxios.stubOnce('GET', /.*/, {
    status: 500,
    response: { body: {}, message: 'an error has occured' },
  });
  await wait();
  expect(lerror).toBeTruthy();
  expect(lerror).toBeInstanceOf(Error);
  expect((lerror! as Error).message).toEqual(
    'Request failed with status code 500',
  );
});
