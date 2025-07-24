import { DataGrid } from '@mui/x-data-grid';
import { useState, useMemo } from 'react';
import DialogDetail from './DialogDetail';

export default function DialogTable({ rows }) {
  const [openRow, setOpenRow] = useState(null);

  // Flatten scenes into individual dialogues for table display
  const dialogues = useMemo(() => {
    const flatDialogues = [];
    rows.forEach(scene => {
      scene.dialogues?.forEach((dialogue, index) => {
        flatDialogues.push({
          ...dialogue,
          id: `${scene.scene_id}_${index}`,
          scene_setting: scene.setting,
          participants: scene.participants
        });
      });
    });
    return flatDialogues;
  }, [rows]);

  const columns = useMemo(() => [
    { field: 'character', headerName: 'Character', width: 140 },
    { field: 'addressee', headerName: 'To', width: 120 },
    { field: 'chapter_number', headerName: 'Chapter', width: 100 },
    { field: 'emotion', headerName: 'Emotion', width: 120 },
    { field: 'dialogue', headerName: 'Dialogue', flex: 1 },
  ], []);

  return (
    <>
      <DataGrid
        autoHeight
        rows={dialogues}
        columns={columns}
        pageSize={10}
        getRowId={(r) => r.id}
        onRowClick={(p) => setOpenRow(p.row)}
        disableSelectionOnClick
      />

      <DialogDetail row={openRow} onClose={() => setOpenRow(null)} />
    </>
  );
}