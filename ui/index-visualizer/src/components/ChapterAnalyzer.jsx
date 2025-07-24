import { useState } from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import ChapterTable from './ChapterTable';
import ChapterAggregateDashboard from './ChapterAggregateDashboard';

export default function ChapterAnalyzer({ chapters }) {
  const [tab, setTab] = useState(0);

  if (!chapters || chapters.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
        No chapter data available
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Chapter List" />
          <Tab label="Chapter Analytics" />
        </Tabs>
      </Box>

      {tab === 0 && <ChapterTable rows={chapters} />}
      {tab === 1 && <ChapterAggregateDashboard rows={chapters} />}
    </Box>
  );
}