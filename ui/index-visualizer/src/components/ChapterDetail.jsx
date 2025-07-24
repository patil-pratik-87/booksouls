import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Chip, Box } from '@mui/material';

export default function ChapterDetail({ row, onClose }) {
  if (!row) return null;

  return (
    <Dialog open={!!row} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Chapter {row.chapter_number}: {row.chapter_title}
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Summary</Typography>
          <Typography variant="body2" paragraph>
            {row.summary || 'No summary available'}
          </Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Statistics</Typography>
          <Typography variant="body2">
            Pages: {row.start_page} - {row.end_page} | 
            Tokens: {row.token_count?.toLocaleString()} | 
            Words: {row.word_count?.toLocaleString()} | 
            Sections: {row.section_count}
          </Typography>
        </Box>

        {row.entities && row.entities.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>Characters/Entities</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {row.entities.map((entity, i) => (
                <Chip key={i} label={entity} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {row.themes && row.themes.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>Themes</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {row.themes.map((theme, i) => (
                <Chip key={i} label={theme} size="small" color="primary" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        <Box>
          <Typography variant="h6" gutterBottom>Content Preview</Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto' }}>
            {row.content?.substring(0, 1000)}{row.content?.length > 1000 ? '...' : ''}
          </Typography>
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}