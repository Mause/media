import { OptionsComponent } from './OptionsComponent';
import { RouteTitle } from './RouteTitle';

export function TvOptionsComponent() {
  return (
    <RouteTitle title="TV Options">
      <OptionsComponent type="series" />
    </RouteTitle>
  );
}
