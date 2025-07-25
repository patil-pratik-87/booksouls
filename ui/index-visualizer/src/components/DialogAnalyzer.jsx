import { useState } from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import DialogTable from './DialogTable';
import DialogAggregateDashboard from './DialogAggregateDashboard';
import { FILTER_DEFAULTS } from '../utils/dialogFilters';

export default function DialogAnalyzer({ dialogs }) {
  const [activeTab, setActiveTab] = useState(0);
  const [filters, setFilters] = useState(FILTER_DEFAULTS);

  const updateFilter = (filterType, value) => {
    setFilters(prev => ({ ...prev, [filterType]: value }));
  };

  const switchToDialogList = () => setActiveTab(0);

  if (!dialogs?.length) {
    return (
      <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
        No dialog data available
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab label="Dialog List" />
          <Tab label="Dialog Analytics" />
        </Tabs>
      </Box>

      {activeTab === 0 && (
        <DialogTable rows={dialogs} filters={filters} />
      )}
      {activeTab === 1 && (
        <DialogAggregateDashboard 
          rows={dialogs} 
          filters={filters} 
          onFilterChange={updateFilter}
          onSwitchToDialogList={switchToDialogList}
        />
      )}
    </Box>
  );
}