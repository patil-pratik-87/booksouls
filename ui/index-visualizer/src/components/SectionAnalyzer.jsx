import { useState } from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import SectionTable from './SectionTable';
import AggregateDashboard from './AggregateDashboard';

export default function SectionAnalyzer({ sections }) {
  const [tab, setTab] = useState(0);

  if (!sections || sections.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
        No section data available
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Section List" />
          <Tab label="Section Analytics" />
        </Tabs>
      </Box>

      {tab === 0 && <SectionTable rows={sections} />}
      {tab === 1 && <AggregateDashboard rows={sections} />}
    </Box>
  );
}