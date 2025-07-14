import { render } from '@testing-library/react';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { ErrorBoundary } from 'react-error-boundary';
import { http, HttpResponse } from 'msw';

import AxiosErrorCatcher from './AxiosErrorCatcher';
import { server } from './msw';
import { waitForRequests } from './test.utils';

beforeEach(() => {
  vitest.spyOn(console, 'error').mockImplementation(() => {});
});

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
  server.use(
    http.get(/.*/, () =>
      HttpResponse.json(
        { body: {}, message: 'an error has occured' },
        {
          status: 500,
        },
      ),
    ),
  );

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

  await waitForRequests();

  expect(lerror).toBeTruthy();
  expect(lerror).toBeInstanceOf(Error);
  expect((lerror! as Error).message).toEqual(
    'Request failed with status code 500',
  );
});
