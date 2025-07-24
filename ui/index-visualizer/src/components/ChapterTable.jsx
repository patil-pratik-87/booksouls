import { DataGrid } from '@mui/x-data-grid';
import { useState, useMemo } from 'react';
import ChapterDetail from './ChapterDetail';

export default function ChapterTable({ rows }) {
  const [openRow, setOpenRow] = useState(null);

  const columns = useMemo(() => [
    { field: 'chapter_id', headerName: 'Chapter ID', flex: 1 },
    { field: 'chapter_number', headerName: 'Chapter', width: 100 },
    { field: 'chapter_title', headerName: 'Title', flex: 1 },
    { field: 'token_count', headerName: 'Tokens', width: 100, type: 'number' },
    { field: 'word_count', headerName: 'Words', width: 100, type: 'number' },
    { field: 'section_count', headerName: 'Sections', width: 100, type: 'number' },
  ], []);

  return (
    <>
      <DataGrid
        autoHeight
        rows={rows}
        columns={columns}
        pageSize={10}
        getRowId={(r) => r.chapter_id}
        onRowClick={(p) => setOpenRow(p.row)}
        disableSelectionOnClick
      />

      <ChapterDetail row={openRow} onClose={() => setOpenRow(null)} />
    </>
  );
}