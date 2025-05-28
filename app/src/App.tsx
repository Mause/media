import { styled } from '@mui/material/styles';

import './App.css';
import { ParentComponent } from './streaming';

const AddMargin = styled('div')({
  margin: '0 5%',
});

function App() {
  return (
    <AddMargin>
      <ParentComponent />
    </AddMargin>
  );
}

export default App;
