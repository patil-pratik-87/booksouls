import {
  Dialog, DialogTitle, DialogContent, DialogContentText,
  Chip, Stack, Typography, IconButton, Grid, Box
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

export default function SectionDetail({ row, onClose }) {
  return (
    <Dialog open={Boolean(row)} onClose={onClose} maxWidth="md" fullWidth>
      {row && (
        <>
          <DialogTitle sx={{ m: 0, p: 2 }}>
            Section: {row.section_id}
            <IconButton
              aria-label="close"
              onClick={onClose}
              sx={{ position: 'absolute', right: 8, top: 8 }}
            >
              <CloseIcon />
            </IconButton>
          </DialogTitle>

          <DialogContent dividers sx={{ p: 0 }}>
            <Grid container sx={{ height: '70vh' }}>
              {/* Left side - Content */}
              <Grid item xs={8} sx={{ p: 2, borderRight: 1, borderColor: 'divider' }}>
                <DialogContentText component="div">
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{row.content}</Typography>
                </DialogContentText>
              </Grid>
              
              {/* Right side - Metadata */}
              <Grid item xs={4} sx={{ p: 2 }}>
                <Stack spacing={2}>
                  <AttributeList title="Entities" items={row.entities} />
                  <AttributeList title="Themes" items={row.themes} />
                  <AttributeList title="Metadata" items={[
                    `Chapter: ${row.chapter_number}`,
                    `Semantic type: ${row.semantic_type}`,
                    `Tokens: ${row.token_count}`,
                    `Words: ${row.word_count}`,
                  ]} />
                </Stack>
              </Grid>
            </Grid>
          </DialogContent>
        </>
      )}
    </Dialog>
  );
}

function AttributeList({ title, items = [] }) {
  if (!items.length) return null;
  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>{title}</Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        {items.map((x) => <Chip key={x} label={x} size="small" />)}
      </Stack>
    </Box>
  );
}
