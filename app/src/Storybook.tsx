import ContextMenu from './ContextMenu';
import MenuItem from '@mui/material/MenuItem';
import Accordian from '@mui/material/Accordian';
import AccordianDetails from '@mui/material/AccordianDetails';
import AccordianSummary from '@mui/material/AccordianSummary';
import { SimpleDiagnosticDisplay } from './DiagnosticsComponent';

export default function Storybook() {
  const sortedMovies = {
    true: [
      {
        id: 0,
        download: {
          title: 'Storybook'
        }
      }
    ]
  };
  
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
      <Accordion>
        <AccordionSummary>
          <span>Finished downloads ({sortedMovies.true.length})</span>
        </AccordionSummary>
        <AccordionDetails>
          <ul>
            {(sortedMovies.true || []).map((movie) => (
              <li key={movie.id}>
                <span>{movie.download.title}</span>
              </li>
            ))}
          </ul>
        </AccordionDetails>
      </Accordion>
    </div>
  );
}
