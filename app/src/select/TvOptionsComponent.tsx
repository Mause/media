import { RouteTitle } from '../components';

import { OptionsComponent } from './OptionsComponent';

export default function TvOptionsComponent() {
  return (
    <RouteTitle title="TV Options">
      <OptionsComponent type="series" />
    </RouteTitle>
  );
}
