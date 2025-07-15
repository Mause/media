import MenuItem from '@mui/material/MenuItem';
import { useEffect, useState } from 'react';
import { useSWRConfig } from 'swr';
import { en_AU, Faker, en, base } from '@faker-js/faker';
import { Box, Tab, Tabs } from '@mui/material';

import { OpenPlex, Progress } from './render';
import ContextMenu from './ContextMenu';
import { SimpleDiagnosticDisplay } from './DiagnosticsComponent';
import { PureDiscoveryComponent } from './DiscoveryComponent';
import { RouteTitle } from './RouteTitle';

function DiscoveryStory() {
  const { mutate } = useSWRConfig();

  void mutate('tmdb/configuration', {
    images: {
      poster_sizes: ['w800'],
    },
  });
  const cats = [
    'neo',
    'millie',
    'millie_neo',
    'neo_banana',
    'neo_2',
    'bella',
    'poppy',
    'louie',
  ];

  const faker = new Faker({
    locale: [en_AU, en, base],
    seed: 42,
  });

  return (
    <PureDiscoveryComponent
      data={{
        results: Array.from({ length: 12 }, (_, id) => ({
          id,
          title: `Hello World - ${id}`,
          release_date: `2022-01-${String(id + 1).padStart(2, '0')}`,
          poster_path: cats[id % cats.length],
          overview: faker.lorem.sentence(10),
        })),
      }}
      error={undefined}
      isValidating={false}
      build={(_base, size, poster_path) => {
        const width =
          size === 'original' ? 400 : Number.parseInt(size.substring(1));
        const height = width * 1.5;

        return `https://placecats.com/${poster_path}/${width}/${height}`;
      }}
    />
  );
}
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}
function CustomTabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export function Storybook() {
  const [percentDone, setPercentDone] = useState(0.5);
  useEffect(() => {
    const interval = setInterval(() => {
      setPercentDone(Math.random());
    }, 1000);
    return () => clearInterval(interval);
  });

  const [value, setValue] = useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <RouteTitle title="Storybook">
      <Tabs value={value} onChange={handleChange}>
        <Tab label="Discover"></Tab>
        <Tab label="Misc" data-testid="misc"></Tab>
      </Tabs>
      <CustomTabPanel index={0} value={value}>
        <DiscoveryStory />
      </CustomTabPanel>
      <CustomTabPanel index={1} value={value}>
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
        <OpenPlex download={{ tmdb_id: 0 }} type='movie' />
      </CustomTabPanel>
    </RouteTitle>
  );
}
