import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Chip, Box } from '@mui/material';

export default function DialogDetail({ row, onClose }) {
  if (!row) return null;

  return (
    <Dialog open={!!row} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Dialogue: {row.character} → {row.addressee}
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Scene Information</Typography>
          <Typography variant="body2">
            Chapter: {row.chapter_number} | Scene: {row.scene_id}
          </Typography>
          {row.scene_setting && (
            <Typography variant="body2">
              Setting: {row.scene_setting}
            </Typography>
          )}
          {row.participants && row.participants.length > 0 && (
            <Typography variant="body2">
              Participants: {row.participants.join(', ')}
            </Typography>
          )}
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Dialogue</Typography>
          <Typography variant="body1" sx={{ fontStyle: 'italic', p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
            "{row.dialogue}"
          </Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Emotional Context</Typography>
          <Chip label={row.emotion || 'neutral'} color="primary" variant="outlined" />
        </Box>

        {row.actions && row.actions.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>Actions</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {row.actions.map((action, i) => (
                <Chip key={i} label={action} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {row.context && (
          <Box>
            <Typography variant="h6" gutterBottom>Context</Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', maxHeight: 150, overflow: 'auto' }}>
              {row.context}
            </Typography>
          </Box>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}