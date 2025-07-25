import { DataGrid } from '@mui/x-data-grid';
import { useState, useMemo } from 'react';
import { Box, Chip, Typography } from '@mui/material';
import DialogDetail from './DialogDetail';
import { 
  flattenDialogues, 
  applyDialogueFilters, 
  getActiveFilterLabels 
} from '../utils/dialogFilters';

const COLUMNS = [
  { field: 'character', headerName: 'Character', width: 140 },
  { field: 'addressee', headerName: 'To', width: 120 },
  { field: 'chapter_number', headerName: 'Chapter', width: 100 },
  { field: 'emotion', headerName: 'Emotion', width: 120 },
  { field: 'dialogue', headerName: 'Dialogue', flex: 1 },
];

export default function DialogTable({ rows, filters }) {
  const [selectedRow, setSelectedRow] = useState(null);

  const allDialogues = useMemo(() => flattenDialogues(rows), [rows]);
  const filteredDialogues = useMemo(() => applyDialogueFilters(allDialogues, filters), [allDialogues, filters]);
  const activeFilterLabels = getActiveFilterLabels(filters);
  
  const hasActiveFilters = activeFilterLabels.length > 0;

  return (
    <>
      {hasActiveFilters && (
        <Box sx={{ p: 2, backgroundColor: '#f5f5f5', borderRadius: 1, mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Active Filters ({filteredDialogues.length} of {allDialogues.length} dialogues):
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {activeFilterLabels.map((label, index) => (
              <Chip key={index} label={label} size="small" color="primary" variant="outlined" />
            ))}
          </Box>
        </Box>
      )}
      
      <DataGrid
        autoHeight
        rows={filteredDialogues}
        columns={COLUMNS}
        pageSize={10}
        getRowId={(row) => row.id}
        onRowClick={(params) => setSelectedRow(params.row)}
        disableSelectionOnClick
      />

      <DialogDetail 
        row={selectedRow} 
        onClose={() => setSelectedRow(null)} 
      />
    </>
  );
}