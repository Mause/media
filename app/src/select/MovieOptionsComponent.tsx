import { RouteTitle } from '../components';

import { OptionsComponent } from './OptionsComponent';

export default function MovieOptionsComponent() {
  return (
    <RouteTitle title="Movie Options">
      <OptionsComponent type="movie" />
    </RouteTitle>
  );
}
