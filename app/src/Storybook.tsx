import MenuItem from '@mui/material/MenuItem';
import { useEffect, useState } from 'react';

import { Progress } from './render';
import ContextMenu from './ContextMenu';
import { SimpleDiagnosticDisplay } from './DiagnosticsComponent';
import { DiscoveryComponent } from './DiscoverComponent';
import { RouteTitle } from './RouteTitle';
import { useSWRConfig } from 'swr';

function DiscoveryStory() {
  const { mutate } = useSWRConfig();

  mutate('tmdb/configuration', {});
  mutate('discover', {});

  return <DiscoveryComponent />;
}

export function Storybook() {
  const [percentDone, setPercentDone] = useState(0.5);
  useEffect(() => {
    const interval = setInterval(() => {
      setPercentDone(Math.random());
    }, 1000);
    return () => clearInterval(interval);
  });

  return (
    <RouteTitle title="Storybook">
      <ContextMenu>
        <MenuItem component="a" href="http://google.com" target="_blank">
          Hello
        </MenuItem>
        <MenuItem>World</MenuItem>
      </ContextMenu>
      <hr />
      <SimpleDiagnosticDisplay
        component="Storybook"
        data={[
          {
            component_name: 'Storybook',
            component_type: 'datastore',
            status: 'pass',
            time: '2022-01-01T10:10:00',
            output: {
              hello: 'world',
            },
          },
        ]}
        error={undefined}
        isValidating={false}
      />
      <hr />
      <Progress
        torrents={{
          TRANSMISSION_ID: {
            id: 1,
            percentDone,
            eta: 3600,
            hashString: '1234567890abcdef1234567890abcdef12345678',
            files: [],
          },
        }}
        item={{
          download: {
            transmission_id: 'TRANSMISSION_ID',
          },
        }}
      />
      <hr />
      <DiscoveryStory />
    </RouteTitle>
  );
}
