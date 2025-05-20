import MenuItem from '@mui/material/MenuItem';

import ContextMenu from './ContextMenu';
import { SimpleDiagnosticDisplay } from './DiagnosticsComponent';

export default function Storybook() {
  return (
    <div>
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
    </div>
  );
}
