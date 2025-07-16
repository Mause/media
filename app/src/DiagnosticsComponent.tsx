import ReactLoading from 'react-loading';
import useSWR from 'swr';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircle } from '@fortawesome/free-solid-svg-icons';

import type { paths } from './schema';
import type { GetResponse } from './utils';
import { RouteTitle } from './components';

type DiagnosticsRoot = GetResponse<paths['/api/diagnostics']>;
type HealthcheckResponse = GetResponse<
  paths['/api/diagnostics/{component_name}']
>;
type Healthcheck = HealthcheckResponse[0];

function getColour(status?: Healthcheck['status']) {
  switch (status) {
    case 'pass':
      return 'green';
    case 'warn':
      return 'yellow';
    case 'fail':
      return 'red';
    default:
      return 'grey';
  }
}

function SingleDiagnostic({ component }: { component: string }) {
  const { error, data, isValidating } = useSWR<HealthcheckResponse, Error>(
    `diagnostics/${component}`,
  );

  return (
    <SimpleDiagnosticDisplay
      component={component}
      error={error}
      data={data}
      isValidating={isValidating}
    />
  );
}

export function SimpleDiagnosticDisplay({
  component,
  data,
  error,
  isValidating,
}: {
  component: string;
  data?: HealthcheckResponse;
  error: unknown;
  isValidating: boolean;
}) {
  return (
    <li>
      {component}: {isValidating && <ReactLoading type="balls" color="#000" />}
      <ul>
        {data?.map((item, i) => (
          <li key={i}>
            <FontAwesomeIcon
              icon={faCircle}
              className={getColour(item.status)}
            />
            <pre>
              <code>
                {JSON.stringify(
                  {
                    component_type: item.component_type,
                    time: item.time,
                    output: item.output,
                  },
                  null,
                  2,
                )}
              </code>
            </pre>
          </li>
        ))}
      </ul>
      {error ? (
        <pre>
          <code>{JSON.stringify(error, null, 2)}</code>
        </pre>
      ) : undefined}
    </li>
  );
}

export function DiagnosticsComponent() {
  const { error, data, isValidating } = useSWR<DiagnosticsRoot, Error>(
    'diagnostics',
  );

  return (
    <RouteTitle title="Diagnostics">
      <h3>Diagnostics: Media {data?.version}</h3>

      {isValidating && <ReactLoading type="balls" color="#000" />}

      {error && (
        <pre>
          <code>{JSON.stringify({ error }, null, 2)}</code>
        </pre>
      )}

      <ul>
        {data?.checks.map((component) => (
          <li key={component}>
            <SingleDiagnostic component={component} />
          </li>
        ))}
      </ul>
    </RouteTitle>
  );
}
