import { OptionsComponent } from './OptionsComponent';
import { RouteTitle } from './RouteTitle';

export function MovieOptionsComponent() {
  return (
    <RouteTitle title="Movie Options">
      <OptionsComponent type="movie" />
    </RouteTitle>
  );
}
