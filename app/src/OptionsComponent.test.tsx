import React from 'react';
import { render, act, wait } from '@testing-library/react';
import { OptionsComponent } from './OptionsComponent';
import { swrConfig } from './streaming';
import { MemoryRouter, Route } from 'react-router-dom';

import EventSource from 'eventsource';

let sources = [];
class ES {
  constructor() {
    sources.push(this);
    console.warn(this);
  }
  addEventListener(name, ls) {
    this.ls = ls;
  }
  close() {}
}

Object.defineProperty(window, 'EventSource', {
  value: ES, //EventSource,
});

test('OptionsComponent', async () => {
  await act(async () => {
    const el = render(
      <MemoryRouter>
        <Route p>
          <OptionsComponent />
        </Route>
      </MemoryRouter>,
    );
    expect(el.container).toMatchSnapshot();

    await wait(1);

    sources[0].ls({ data: '[{}]' });
  });
});
