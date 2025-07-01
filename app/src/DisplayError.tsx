import * as _ from 'lodash-es';
import { Alert } from '@mui/material';

export function DisplayError(props: { error: Error; message?: string }) {
  const message =
    _.get(props.error, 'response.data.message') ||
    (props.message || 'Unable to connect to transmission') +
      ': ' +
      props.error.toString();

  return (
    <div>
      <br />
      <Alert color="warning">
        <span data-testid="errorMessage">{message}</span>
      </Alert>
    </div>
  );
}
