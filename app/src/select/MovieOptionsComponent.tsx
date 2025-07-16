import { RouteTitle } from '../RouteTitle';

import { OptionsComponent } from './OptionsComponent';

export function MovieOptionsComponent() {
  return (
    <RouteTitle title="Movie Options">
      <OptionsComponent type="movie" />
    </RouteTitle>
  );
}
