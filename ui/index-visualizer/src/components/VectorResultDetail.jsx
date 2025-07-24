import {
  Dialog, DialogTitle, DialogContent, DialogContentText,
  Chip, Stack, Typography, IconButton, Grid, Box
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

export default function VectorResultDetail({ result, onClose }) {
  if (!result) return null;

  return (
    <Dialog open={Boolean(result)} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ m: 0, p: 2 }}>
        Document: {result.document_id}
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
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {result.content}
              </Typography>
            </DialogContentText>
          </Grid>
          
          {/* Right side - Metadata */}
          <Grid item xs={4} sx={{ p: 2 }}>
            <Stack spacing={2}>
              <AttributeList title="Query Match" items={[
                `Similarity: ${(result.similarity * 100).toFixed(1)}%`
              ]} />
              
              <AttributeList title="Content Info" items={[
                `Chapter: ${result.metadata?.chapter_number || 'Unknown'}`,
                `Section: ${result.metadata?.section_index || 'Unknown'}`,
                `Type: ${result.metadata?.semantic_type || 'Unknown'}`,
              ].filter(item => !item.includes('Unknown'))} />

              {result.metadata?.character && (
                <AttributeList title="Character" items={[result.metadata.character]} />
              )}

              {result.metadata?.emotion && (
                <AttributeList title="Emotion" items={[result.metadata.emotion]} />
              )}

              {result.metadata?.themes && (
                <AttributeList title="Themes" items={result.metadata.themes} />
              )}

              {result.metadata?.entities && (
                <AttributeList title="Entities" items={result.metadata.entities} />
              )}
            </Stack>
          </Grid>
        </Grid>
      </DialogContent>
    </Dialog>
  );
}

function AttributeList({ title, items = [] }) {
  // Ensure items is always an array
  const itemsArray = Array.isArray(items) ? items : [items].filter(Boolean);
  
  if (!itemsArray.length) return null;
  
  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>{title}</Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        {itemsArray.map((item, index) => (
          <Chip 
            key={`${String(item)}-${index}`} 
            label={String(item)} 
            size="small" 
          />
        ))}
      </Stack>
    </Box>
  );
}