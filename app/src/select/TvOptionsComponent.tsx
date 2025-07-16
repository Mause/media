import { RouteTitle } from '../RouteTitle';

import { OptionsComponent } from './OptionsComponent';

export function TvOptionsComponent() {
  return (
    <RouteTitle title="TV Options">
      <OptionsComponent type="series" />
    </RouteTitle>
  );
}
