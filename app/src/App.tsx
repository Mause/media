import { useSentryToolbar } from '@sentry/toolbar';

import './App.css';
import { ParentComponent } from './streaming';

const App = () => {
  useSentryToolbar({
    // Remember to conditionally enable the Toolbar.
    // This will reduce network traffic for users
    // who do not have credentials to login to Sentry.
    enabled: true,
    initProps: {
      organizationSlug: 'elliana-may',
      projectIdOrSlug: '1869914',
    },
  });
  return <ParentComponent />;
};

export default App;
