export function summarise(sections) {
  const total = sections.length;
  const tokens = sections.reduce((s, r) => s + (r.token_count ?? 0), 0);
  const words  = sections.reduce((s, r) => s + (r.word_count  ?? 0), 0);

  const countBy = (key) =>
    sections.reduce((acc, r) => {
      const val = r[key];
      if (Array.isArray(val)) val.forEach((v) => acc[v] = (acc[v] ?? 0) + 1);
      else if (val) acc[val] = (acc[val] ?? 0) + 1;
      return acc;
    }, {});

  return {
    total,
    tokens,
    words,
    byType:  countBy('semantic_type'),
    byTheme: countBy('themes'),
    byEntity: countBy('entities'),
  };
}

export function summariseChapters(chapters) {
  const total = chapters.length;
  const tokens = chapters.reduce((s, r) => s + (r.token_count ?? 0), 0);
  const words = chapters.reduce((s, r) => s + (r.word_count ?? 0), 0);
  const sections = chapters.reduce((s, r) => s + (r.section_count ?? 0), 0);

  const countBy = (key) =>
    chapters.reduce((acc, r) => {
      const val = r[key];
      if (Array.isArray(val)) val.forEach((v) => acc[v] = (acc[v] ?? 0) + 1);
      else if (val) acc[val] = (acc[val] ?? 0) + 1;
      return acc;
    }, {});

  // Calculate average chapter length
  const avgTokensPerChapter = total > 0 ? Math.round(tokens / total) : 0;
  const avgWordsPerChapter = total > 0 ? Math.round(words / total) : 0;

  return {
    total,
    tokens,
    words,
    sections,
    avgTokensPerChapter,
    avgWordsPerChapter,
    byTheme: countBy('themes'),
    byEntity: countBy('entities'),
  };
}

export function summariseDialogs(scenes) {
  const totalScenes = scenes.length;
  const totalDialogues = scenes.reduce((s, scene) => s + (scene.dialogues?.length ?? 0), 0);
  
  // Flatten all dialogues for analysis
  const allDialogues = scenes.flatMap(scene => scene.dialogues || []);
  
  const countBy = (key) =>
    allDialogues.reduce((acc, dialogue) => {
      const val = dialogue[key];
      if (Array.isArray(val)) val.forEach((v) => acc[v] = (acc[v] ?? 0) + 1);
      else if (val) acc[val] = (acc[val] ?? 0) + 1;
      return acc;
    }, {});

  // Count characters by dialogue frequency
  const characterDialogueCounts = countBy('character');
  
  // Count emotions
  const emotionCounts = countBy('emotion');
  
  // Count chapters with dialogue
  const chaptersWithDialogue = [...new Set(scenes.map(s => s.chapter_number))];

  return {
    totalScenes,
    totalDialogues,
    avgDialoguesPerScene: totalScenes > 0 ? Math.round(totalDialogues / totalScenes * 10) / 10 : 0,
    chaptersWithDialogue: chaptersWithDialogue.length,
    byCharacter: characterDialogueCounts,
    byEmotion: emotionCounts,
  };
}
