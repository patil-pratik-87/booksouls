import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Badge,
  Divider,
  LinearProgress,
  Tooltip
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Psychology as PsychologyIcon,
  EmojiEvents as GoalIcon,
  Mood as MoodIcon,
  ChatBubble as DialogueIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Circle as CircleIcon,
  Star as StarIcon,
  Timeline as TimelineIcon,
  KeyboardArrowDown as ArrowDownIcon
} from '@mui/icons-material';

const CharacterTimeline = ({ character }) => {
  const [expandedPanel, setExpandedPanel] = useState(0);

  const handleAccordionChange = (panel) => (event, isExpanded) => {
    setExpandedPanel(isExpanded ? panel : false);
  };

  const getEmotionColor = (emotion) => {
    const emotionColors = {
      'happy': '#4CAF50',
      'sad': '#2196F3',
      'angry': '#F44336',
      'excited': '#FF9800',
      'calm': '#9C27B0',
      'worried': '#FF5722',
      'confident': '#00BCD4',
      'neutral': '#9E9E9E'
    };
    return emotionColors[emotion?.toLowerCase()] || '#9E9E9E';
  };

  const getTraitChangeIcon = (profile, previousProfile) => {
    if (!previousProfile) return <StarIcon color="primary" />;
    
    const getTraitNames = (traitArray) => {
      if (!Array.isArray(traitArray)) return [];
      return traitArray.map(t => typeof t === 'string' ? t : t.trait).filter(Boolean);
    };
    
    const currentTraits = new Set(getTraitNames(profile.personality_traits));
    const previousTraits = new Set(getTraitNames(previousProfile.personality_traits));
    
    const newTraits = [...currentTraits].filter(trait => !previousTraits.has(trait));
    const lostTraits = [...previousTraits].filter(trait => !currentTraits.has(trait));
    
    if (newTraits.length > lostTraits.length) {
      return <TrendingUpIcon color="success" />;
    } else if (lostTraits.length > newTraits.length) {
      return <TrendingUpIcon color="warning" sx={{ transform: 'rotate(180deg)' }} />;
    } else {
      return <CircleIcon color="action" />;
    }
  };

  const renderTraitComparison = (currentTraits, previousTraits) => {
    const getTraitNames = (traitArray) => {
      if (!Array.isArray(traitArray)) return [];
      return traitArray.map(t => typeof t === 'string' ? t : t.trait).filter(Boolean);
    };
    
    const currentTraitNames = getTraitNames(currentTraits);
    const previousTraitNames = previousTraits ? getTraitNames(previousTraits) : [];
    
    if (!previousTraits) {
      return (
        <Box>
          <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
            Initial Traits:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {currentTraitNames.map((trait) => (
              <Chip key={trait} label={trait} size="small" color="primary" />
            ))}
          </Box>
        </Box>
      );
    }
    
    const currentSet = new Set(currentTraitNames);
    const previousSet = new Set(previousTraitNames);
    
    const newTraits = [...currentSet].filter(trait => !previousSet.has(trait));
    const lostTraits = [...previousSet].filter(trait => !currentSet.has(trait));
    const unchangedTraits = [...currentSet].filter(trait => previousSet.has(trait));
    
    return (
      <Box>
        {unchangedTraits.length > 0 && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" sx={{ mb: 0.5, color: 'text.secondary' }}>
              Continuing Traits:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {unchangedTraits.map((trait) => (
                <Chip key={trait} label={trait} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}
        
        {newTraits.length > 0 && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" sx={{ mb: 0.5, color: 'success.main' }}>
              New Traits:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {newTraits.map((trait) => (
                <Chip key={trait} label={trait} size="small" color="success" />
              ))}
            </Box>
          </Box>
        )}
        
        {lostTraits.length > 0 && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" sx={{ mb: 0.5, color: 'error.main' }}>
              Lost Traits:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {lostTraits.map((trait) => (
                <Chip key={trait} label={trait} size="small" color="error" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  const renderChapterCard = (profile, index, previousProfile) => {
    return (
      <Card 
        key={profile.chapter_number}
        sx={{ 
          mb: 2,
          border: expandedPanel === index ? '2px solid' : '1px solid',
          borderColor: expandedPanel === index ? 'primary.main' : 'divider'
        }}
      >
        <Accordion 
          expanded={expandedPanel === index} 
          onChange={handleAccordionChange(index)}
          sx={{ boxShadow: 'none', '&:before': { display: 'none' } }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              <Box sx={{ mr: 2 }}>
                {getTraitChangeIcon(profile, previousProfile)}
              </Box>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h6">
                  Chapter {profile.chapter_number}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 0.5 }}>
                  <Chip
                    icon={<DialogueIcon />}
                    label={`${profile.dialogue_count} dialogues`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    icon={<MoodIcon />}
                    label={profile.emotional_state}
                    size="small"
                    sx={{
                      bgcolor: getEmotionColor(profile.emotional_state) + '20',
                      color: getEmotionColor(profile.emotional_state),
                      borderColor: getEmotionColor(profile.emotional_state)
                    }}
                  />
                  <Box sx={{ flexGrow: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={(profile.dialogue_count / Math.max(...character.profiles.map(p => p.dialogue_count))) * 100}
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>
                </Box>
              </Box>
            </Box>
          </AccordionSummary>
          
          <AccordionDetails>
            <Grid container spacing={3}>
              {/* Personality Traits */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, height: '100%' }}>
                  <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <PsychologyIcon sx={{ mr: 1 }} />
                    Personality Development
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  {renderTraitComparison(profile.personality_traits, previousProfile?.personality_traits)}
                </Paper>
              </Grid>

              {/* Motivations */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, height: '100%' }}>
                  <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <GoalIcon sx={{ mr: 1 }} />
                    Motivations & Goals
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <List dense>
                    {profile.motivations.map((motivation, idx) => (
                      <ListItem key={idx} sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <CircleIcon sx={{ fontSize: 8 }} />
                        </ListItemIcon>
                        <ListItemText primary={motivation} />
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              </Grid>

              {/* Speech Style */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, height: '100%' }}>
                  <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <DialogueIcon sx={{ mr: 1 }} />
                    Speech Style
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Vocabulary: 
                      <Chip 
                        label={profile.speech_style?.vocabulary || 'Unknown'} 
                        size="small" 
                        sx={{ ml: 1 }}
                      />
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Sentence Style: 
                      <Chip 
                        label={profile.speech_style?.sentence_style || 'Unknown'} 
                        size="small" 
                        sx={{ ml: 1 }}
                      />
                    </Typography>
                  </Box>
                  {profile.speech_style?.verbal_tics && profile.speech_style.verbal_tics.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        Verbal Tics:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {profile.speech_style.verbal_tics.map((tic, idx) => (
                          <Chip 
                            key={idx} 
                            label={`"${tic}"`} 
                            size="small" 
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                  {profile.speech_style?.unique_phrases && profile.speech_style.unique_phrases.length > 0 && (
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        Unique Phrases:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {profile.speech_style.unique_phrases.map((phrase, idx) => (
                          <Chip 
                            key={idx} 
                            label={`"${phrase}"`} 
                            size="small" 
                            variant="outlined"
                            color="primary"
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Paper>
              </Grid>

              {/* Relationships */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, height: '100%' }}>
                  <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <PeopleIcon sx={{ mr: 1 }} />
                    Key Relationships
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  {Object.keys(profile.key_relationships || {}).length > 0 ? (
                    <List dense>
                      {Object.entries(profile.key_relationships).map(([person, relationshipObj], idx) => {
                        const relationshipText = typeof relationshipObj === 'string' 
                          ? relationshipObj 
                          : relationshipObj.dynamic || 'Unknown relationship';
                        const trustLevel = relationshipObj.trust_level;
                        
                        return (
                          <ListItem key={idx} sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 32 }}>
                              <PeopleIcon sx={{ fontSize: 16 }} />
                            </ListItemIcon>
                            <ListItemText 
                              primary={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="body2" fontWeight="medium">
                                    {person}
                                  </Typography>
                                  {trustLevel && (
                                    <Chip 
                                      label={`Trust: ${trustLevel}/10`} 
                                      size="small" 
                                      color={trustLevel >= 8 ? 'success' : trustLevel >= 6 ? 'primary' : 'warning'}
                                      variant="outlined"
                                    />
                                  )}
                                </Box>
                              }
                              secondary={
                                <Box>
                                  <Typography variant="caption" color="text.secondary">
                                    {relationshipText}
                                  </Typography>
                                  {relationshipObj.unspoken && (
                                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontStyle: 'italic' }}>
                                      Unspoken: {relationshipObj.unspoken}
                                    </Typography>
                                  )}
                                </Box>
                              }
                            />
                          </ListItem>
                        );
                      })}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No specific relationships identified in this chapter.
                    </Typography>
                  )}
                </Paper>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Card>
    );
  };

  if (!character || !character.profiles) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          No character data available
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h2" color="primary">
                {character.profiles.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Chapters Analyzed
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h2" color="secondary">
                {character.totalDialogues}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Dialogues
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h2" color="success.main">
                {character.commonTraits.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Unique Traits
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Chip
                label={character.evolution.type}
                color={
                  character.evolution.type === 'growth' ? 'success' :
                  character.evolution.type === 'change' ? 'warning' : 'default'
                }
                sx={{ fontSize: '1rem', p: 2 }}
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Character Arc
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <TimelineIcon sx={{ mr: 1 }} />
        Character Development Timeline
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {character.evolution.description}
      </Typography>

      <Box>
        {character.profiles.map((profile, index) => 
          renderChapterCard(profile, index, character.profiles[index - 1])
        )}
      </Box>
    </Box>
  );
};

export default CharacterTimeline;