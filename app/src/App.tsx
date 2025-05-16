import React from 'react';
import './App.css';
import { ParentComponent } from './streaming';
import { Alert, Snackbar } from '@mui/material';
import { useAppUpdated } from './serviceWorkerCallback';

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
