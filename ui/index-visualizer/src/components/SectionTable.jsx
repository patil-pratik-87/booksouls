import { DataGrid } from '@mui/x-data-grid';
import { useState, useMemo } from 'react';
import SectionDetail from './SectionDetail';

export default function SectionTable({ rows }) {
  const [openRow, setOpenRow] = useState(null);

  const columns = useMemo(() => [
    { field: 'section_id', headerName: 'Section ID', flex: 1 },
    { field: 'chapter_number', headerName: 'Chapter', width: 100 },
    { field: 'semantic_type', headerName: 'Type', width: 140 },
    { field: 'token_count', headerName: 'Tokens', width: 100, type: 'number' },
    { field: 'word_count',  headerName: 'Words',  width: 100, type: 'number' },
  ], []);

  return (
    <>
      <DataGrid
        autoHeight
        rows={rows}
        columns={columns}
        pageSize={10}
        getRowId={(r) => r.section_id}
        onRowClick={(p) => setOpenRow(p.row)}
        disableSelectionOnClick
      />

      <SectionDetail row={openRow} onClose={() => setOpenRow(null)} />
    </>
  );
}
