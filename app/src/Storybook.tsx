import ContextMenu from './ContextMenu';
import MenuItem from '@mui/material/MenuItem';

export default function Storybook() {
  return (
    <div>
      <ContextMenu>
        <MenuItem>Hello</MenuItem>
        <MenuItem>World</MenuItem>
      </ContextMenu>
    </div>
  );
}
