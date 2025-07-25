// Shared constants and utilities for dialog filtering and processing

export const FILTER_DEFAULTS = {
  character: 'All Characters',
  emotion: null,
  chapter: 'All Chapters'
};

// Check if any filters are active
export const hasActiveFilters = (filters) => (
  filters.character !== FILTER_DEFAULTS.character || 
  filters.emotion !== FILTER_DEFAULTS.emotion || 
  filters.chapter !== FILTER_DEFAULTS.chapter
);

// Extract unique values from data
export const getUniqueValues = (data, field) => 
  [...new Set(data.map(item => item[field]))].sort();

// Flatten scenes into individual dialogues
export const flattenDialogues = (scenes) => {
  const dialogues = [];
  scenes.forEach(scene => {
    scene.dialogues?.forEach((dialogue, index) => {
      dialogues.push({
        ...dialogue,
        id: `${scene.scene_id}_${index}`,
        scene_setting: scene.setting,
        participants: scene.participants
      });
    });
  });
  return dialogues;
};

// Apply filters to dialogues
export const applyDialogueFilters = (dialogues, filters) => {
  return dialogues.filter(dialogue => {
    if (filters.character !== FILTER_DEFAULTS.character && dialogue.character !== filters.character) {
      return false;
    }
    if (filters.emotion && dialogue.emotion !== filters.emotion) {
      return false;
    }
    if (filters.chapter !== FILTER_DEFAULTS.chapter && dialogue.chapter_number !== filters.chapter) {
      return false;
    }
    return true;
  });
};

// Get active filter labels for display
export const getActiveFilterLabels = (filters) => {
  const labels = [];
  if (filters.character !== FILTER_DEFAULTS.character) {
    labels.push(`Character: ${filters.character}`);
  }
  if (filters.emotion) {
    labels.push(`Emotion: ${filters.emotion}`);
  }
  if (filters.chapter !== FILTER_DEFAULTS.chapter) {
    labels.push(`Chapter: ${filters.chapter}`);
  }
  return labels;
};

// Count occurrences of a field in dialogues
export const countByField = (dialogues, field) => {
  return dialogues.reduce((acc, dialogue) => {
    const value = dialogue[field];
    if (value) acc[value] = (acc[value] || 0) + 1;
    return acc;
  }, {});
};

// Convert counts object to sorted chart data
export const createChartData = (counts, limit = null) => {
  const entries = Object.entries(counts)
    .sort((a, b) => b[1] - a[1]);
  
  if (limit) {
    entries.splice(limit);
  }
  
  return entries.map(([name, value]) => ({ name, value }));
};