import { useState } from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import DialogTable from './DialogTable';
import DialogAggregateDashboard from './DialogAggregateDashboard';

export default function DialogAnalyzer({ dialogs }) {
  const [tab, setTab] = useState(0);

  if (!dialogs || dialogs.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
        No dialog data available
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Dialog List" />
          <Tab label="Dialog Analytics" />
        </Tabs>
      </Box>

      {tab === 0 && <DialogTable rows={dialogs} />}
      {tab === 1 && <DialogAggregateDashboard rows={dialogs} />}
    </Box>
  );
}