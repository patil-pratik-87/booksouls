import { useCallback } from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';

export default function UploadBar({ onLoad }) {
  const handleJSON = useCallback((file) => {
    file.text().then((txt) => {
      try {
        const json = JSON.parse(txt);
        onLoad(json);
      } catch (err) {
        alert('Invalid JSON: ' + err.message);
      }
    });
  }, [onLoad]);

  const onInput = (e) => {
    const file = e.target.files?.[0];
    if (file) handleJSON(file);
  };

  const onDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleJSON(file);
  };

  return (
    <AppBar position="static" sx={{ mb: 2 }} onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          BookSouls Index Visualizer
        </Typography>

        <Button component="label" variant="contained">
          Upload JSON
          <input type="file" accept="application/json" hidden onChange={onInput} />
        </Button>
      </Toolbar>
      <Box sx={{ px: 2, pb: 1, fontSize: 12, opacity: 0.8 }}>
        Drag-and-drop a file onto this bar or use “Upload JSON”.
      </Box>
    </AppBar>
  );
}
