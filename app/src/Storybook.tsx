import ContextMenu from "./ContextMenu";
import MenuItem from "@mui/material/MenuItem";

export default function Storybook() {
  return (
    <div>
      <ContextMenu>
        <MenuItem component="a" href="http://google.com" target="_blank">
          Hello
        </MenuItem>
        <MenuItem>World</MenuItem>
      </ContextMenu>
    </div>
  );
}
