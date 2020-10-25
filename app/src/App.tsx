import React from 'react';
import './App.css';
import { ParentComponent } from './streaming';
import { Alert } from '@material-ui/lab';
import { useAppUpdated } from './serviceWorkerCallback';
import { Snackbar } from '@material-ui/core';

const App = () => {
  const appUpdated = useAppUpdated();

  return (
    <>
      {appUpdated && (
        <Snackbar open={true} autoHideDuration={6000}>
          <Alert severity="success">
            A new version of the app is available, please refresh to update!
          </Alert>
        </Snackbar>
      )}
      <ParentComponent />
    </>
  );
};

export default App;
