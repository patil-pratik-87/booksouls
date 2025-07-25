import { useState } from 'react';
import { CssBaseline, Tabs, Tab, Box } from '@mui/material';
import UploadBar from './components/UploadBar';
import SectionAnalyzer from './components/SectionAnalyzer';
import ChapterAnalyzer from './components/ChapterAnalyzer';
import DialogAnalyzer from './components/DialogAnalyzer';
import VectorQueryInterface from './components/VectorQueryInterface';
import CharacterDashboard from './components/CharacterDashboard';

function App() {
  const [sections, setSections] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [dialogs, setDialogs] = useState([]);
  const [characterProfiles, setCharacterProfiles] = useState({});
  const [tab, setTab] = useState(0);

  const handleDataLoad = (data) => {
    // Handle different types of index data
    if (data.sections) {
      setSections(data.sections);
      // Auto-select sections tab if it's the first data loaded
      if (chapters.length === 0 && dialogs.length === 0) {
        setTab(0);
      }
    }
    if (data.chapters) {
      setChapters(data.chapters);
      // Auto-select chapters tab if it's the first data loaded
      if (sections.length === 0 && dialogs.length === 0) {
        setTab(1);
      }
    }
    if (data.scenes) {
      setDialogs(data.scenes);
      // Auto-select dialogs tab if it's the first data loaded
      if (sections.length === 0 && chapters.length === 0) {
        setTab(2);
      }
    }
    if (data.character_profiles) {
      setCharacterProfiles(data.character_profiles);
      // Auto-select character profiles tab if there are character profiles
      if (Object.keys(data.character_profiles).length > 0) {
        setTab(3);
      }
    }
  };


  return (
    <>
      <CssBaseline />
      <UploadBar onLoad={handleDataLoad} />

      <>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
          <Tabs value={tab} onChange={(_, v) => setTab(v)}>
            <Tab label="Section Index" disabled={sections.length === 0} />
            <Tab label="Chapter Index" disabled={chapters.length === 0} />
            <Tab label="Dialog Index" disabled={dialogs.length === 0} />
            <Tab label="Character Profiles" disabled={Object.keys(characterProfiles).length === 0} />
            <Tab label="Vector Query" />
          </Tabs>
        </Box>

        {tab === 0 && <SectionAnalyzer sections={sections} />}
        {tab === 1 && <ChapterAnalyzer chapters={chapters} />}
        {tab === 2 && <DialogAnalyzer dialogs={dialogs} />}
        {tab === 3 && <CharacterDashboard characterProfiles={characterProfiles} />}
        {tab === 4 && <VectorQueryInterface />}
      </>

    </>
  );
}

export default App;
