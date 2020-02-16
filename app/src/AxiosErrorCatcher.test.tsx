import { act, render } from '@testing-library/react';
import { useEffect, useState } from 'react';
import React from 'react';
import AxiosErrorCatcher from './AxiosErrorCatcher';
import { Route, Router } from 'react-router-dom';
import { mock, wait, useMoxios } from './test.utils';
import { createMemoryHistory } from 'history';
import moxios from 'moxios';
import axios from 'axios';
import ErrorBoundary from 'react-error-boundary';

useMoxios();

function Fake() {
  const [fire, setFire] = useState(false);
  useEffect(() => {
    if (fire) axios.get('/');
      else setFire(true);
  }, [fire]);
  return 'Thing';
}

test('AxiosErrorCatcher', async () => {
  await act(async () => {
    let lerror;
    const el = render(
      <ErrorBoundary onError={(error, stack) => (lerror = error)}>
        <AxiosErrorCatcher>
          <Fake />
        </AxiosErrorCatcher>
      </ErrorBoundary>,
    );

    expect(el).toMatchSnapshot();

    await moxios.stubOnce('GET', /.*/, {
      status: 500,
      response: { body: {}, message: 'an error has occured' },
    });
    await wait();
    expect(lerror).toBeTruthy();
  });
});
