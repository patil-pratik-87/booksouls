import { Grid, Card, CardContent, Typography, FormControl, InputLabel, Select, MenuItem, Button, Box } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { summariseDialogs } from '../utils/stats';
import { 
  FILTER_DEFAULTS, 
  hasActiveFilters, 
  getUniqueValues, 
  flattenDialogues,
  countByField,
  createChartData
} from '../utils/dialogFilters';

const CHART_COLORS = ['#8884d8','#82ca9d','#ffc658','#ff7f50','#8dd1e1','#a4de6c','#d0ed57','#8884d8'];
const SELECTED_COLOR = '#ff4444';
const SELECTED_STROKE = '#cc0000';

const processCharacterData = (scenes, chapterFilter) => {
  let filteredScenes = scenes;
  if (chapterFilter !== FILTER_DEFAULTS.chapter) {
    filteredScenes = scenes.filter(scene => scene.chapter_number === chapterFilter);
  }
  
  const dialogues = flattenDialogues(filteredScenes);
  const counts = countByField(dialogues, 'character');
  return createChartData(counts, 10);
};

const processEmotionData = (scenes, characterFilter, chapterFilter) => {
  let dialogues = flattenDialogues(scenes);
  
  if (characterFilter !== FILTER_DEFAULTS.character) {
    dialogues = dialogues.filter(d => d.character === characterFilter);
  }
  if (chapterFilter !== FILTER_DEFAULTS.chapter) {
    dialogues = dialogues.filter(d => d.chapter_number === chapterFilter);
  }
  
  const counts = countByField(dialogues, 'emotion');
  return createChartData(counts);
};

const createCustomTooltip = (selectedValue) => ({ active, payload }) => {
  if (!active || !payload?.[0]) return null;
  
  const data = payload[0].payload;
  const isSelected = selectedValue === data.name;
  
  return (
    <div style={{ 
      backgroundColor: 'white', 
      padding: '8px', 
      border: '1px solid #ccc',
      borderRadius: '4px'
    }}>
      <p>{`${data.name}: ${data.value}`}</p>
      <p style={{ fontSize: '12px', color: '#666' }}>
        Click to {isSelected ? 'deselect' : 'filter'}
      </p>
    </div>
  );
};

const KPICard = ({ label, value }) => (
  <Card sx={{ textAlign: 'center' }}>
    <CardContent>
      <Typography variant="subtitle2">{label}</Typography>
      <Typography variant="h4">{value.toLocaleString()}</Typography>
    </CardContent>
  </Card>
);

const FilterSection = ({ 
  characters, 
  chapters, 
  emotions, 
  filters, 
  onFilterChange, 
  onClearFilters,
  hasActiveFilters 
}) => (
  <Grid item xs={12}>
    <Card sx={{ p: 2, mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Filters</Typography>
        <Button
          variant="outlined"
          size="small"
          onClick={onClearFilters}
          disabled={!hasActiveFilters}
        >
          Clear All
        </Button>
      </Box>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Character</InputLabel>
            <Select
              value={filters.character}
              label="Character"
              onChange={(e) => onFilterChange('character', e.target.value)}
            >
              {characters.map((character) => (
                <MenuItem key={character} value={character}>
                  {character}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Chapter</InputLabel>
            <Select
              value={filters.chapter}
              label="Chapter"
              onChange={(e) => onFilterChange('chapter', e.target.value)}
            >
              {chapters.map((chapter) => (
                <MenuItem key={chapter} value={chapter}>
                  {chapter === 'All Chapters' ? 'All Chapters' : `Chapter ${chapter}`}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Emotion</InputLabel>
            <Select
              value={filters.emotion || ''}
              label="Emotion"
              onChange={(e) => onFilterChange('emotion', e.target.value || null)}
            >
              <MenuItem value="">All Emotions</MenuItem>
              {emotions.map((emotion) => (
                <MenuItem key={emotion} value={emotion}>
                  {emotion}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </Card>
  </Grid>
);

const ChartSection = ({ 
  title, 
  data, 
  selectedValue, 
  onClick, 
  layout = 'horizontal',
  selectedLabel 
}) => (
  <Grid item xs={12} md={6} height={400}>
    <Typography variant="subtitle1" align="center" gutterBottom>
      {title}
      {selectedValue && (
        <Typography component="span" variant="caption" color="primary">
          {` (Selected: ${selectedValue})`}
        </Typography>
      )}
    </Typography>
    <ResponsiveContainer>
      <BarChart 
        data={data}
        layout={layout === 'vertical' ? 'vertical' : undefined}
        margin={{ left: 60, bottom: layout === 'horizontal' ? 20 : 0 }}
        onClick={onClick}
        style={{ cursor: 'pointer' }}
      >
        {layout === 'vertical' ? (
          <>
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="name" width={120} />
          </>
        ) : (
          <>
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} interval={0} />
            <YAxis />
          </>
        )}
        <Tooltip content={createCustomTooltip(selectedValue)} />
        <Bar dataKey="value">
          {data.map((entry, i) => {
            const isSelected = selectedValue === entry.name;
            return (
              <Cell 
                key={i} 
                fill={isSelected ? SELECTED_COLOR : CHART_COLORS[i % CHART_COLORS.length]}
                stroke={isSelected ? SELECTED_STROKE : 'none'}
                strokeWidth={isSelected ? 2 : 0}
              />
            );
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  </Grid>
);

export default function DialogAggregateDashboard({ rows, filters, onFilterChange, onSwitchToDialogList }) {
  const stats = summariseDialogs(rows);

  // Extract unique values for dropdowns
  const characters = [FILTER_DEFAULTS.character, ...Object.keys(stats.byCharacter).sort()];
  const chapters = [FILTER_DEFAULTS.chapter, ...getUniqueValues(rows, 'chapter_number').sort((a, b) => a - b)];
  const emotions = Object.keys(stats.byEmotion).sort();

  // Process chart data
  const characterData = processCharacterData(rows, filters.chapter);
  const emotionData = processEmotionData(rows, filters.character, filters.chapter);

  // Event handlers
  const handleCharacterBarClick = (data) => {
    if (data?.activePayload?.[0]) {
      const clickedCharacter = data.activePayload[0].payload.name;
      const newCharacter = filters.character === clickedCharacter ? FILTER_DEFAULTS.character : clickedCharacter;
      onFilterChange('character', newCharacter);
      onSwitchToDialogList();
    }
  };

  const handleEmotionBarClick = (data) => {
    if (data?.activePayload?.[0]) {
      const clickedEmotion = data.activePayload[0].payload.name;
      const newEmotion = filters.emotion === clickedEmotion ? FILTER_DEFAULTS.emotion : clickedEmotion;
      onFilterChange('emotion', newEmotion);
      onSwitchToDialogList();
    }
  };

  const handleClearFilters = () => {
    onFilterChange('character', FILTER_DEFAULTS.character);
    onFilterChange('emotion', FILTER_DEFAULTS.emotion);
    onFilterChange('chapter', FILTER_DEFAULTS.chapter);
  };

  const filtersActive = hasActiveFilters(filters);

  return (
    <Grid container spacing={2} sx={{ p: 2 }}>
      <FilterSection
        characters={characters}
        chapters={chapters}
        emotions={emotions}
        filters={filters}
        onFilterChange={onFilterChange}
        onClearFilters={handleClearFilters}
        hasActiveFilters={filtersActive}
      />

      {/* KPI Cards */}
      <Grid item xs={12} sm={3}>
        <KPICard label="Scenes" value={stats.totalScenes} />
      </Grid>
      <Grid item xs={12} sm={3}>
        <KPICard label="Total dialogues" value={stats.totalDialogues} />
      </Grid>
      <Grid item xs={12} sm={3}>
        <KPICard label="Avg dialogues/scene" value={stats.avgDialoguesPerScene} />
      </Grid>
      <Grid item xs={12} sm={3}>
        <KPICard label="Chapters with dialogue" value={stats.chaptersWithDialogue} />
      </Grid>

      {/* Charts */}
      <ChartSection
        title="Character Dialogue Frequency"
        data={characterData}
        selectedValue={filters.character !== FILTER_DEFAULTS.character ? filters.character : null}
        onClick={handleCharacterBarClick}
        layout="vertical"
      />

      <ChartSection
        title="Emotions Histogram"
        data={emotionData}
        selectedValue={filters.emotion}
        onClick={handleEmotionBarClick}
        layout="horizontal"
      />
    </Grid>
  );
}