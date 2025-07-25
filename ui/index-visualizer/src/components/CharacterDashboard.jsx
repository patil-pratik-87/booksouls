import React, { useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemText,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress
} from '@mui/material';
import {
  Person as PersonIcon,
  Psychology as PsychologyIcon,
  EmojiEvents as GoalIcon,
  ChatBubble as DialogueIcon,
  Timeline as TimelineIcon,
  ExpandMore as ExpandMoreIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import CharacterTimeline from './CharacterTimeline';

const CharacterDashboard = ({ characterProfiles }) => {
  const [selectedCharacter, setSelectedCharacter] = useState('');
  const [viewMode, setViewMode] = useState('overview'); // 'overview', 'timeline', 'comparison'

  // Helper functions (defined before useMemo)
  const getMostCommonTraits = (profiles) => {
    const traitCounts = {};
    profiles.forEach(profile => {
      if (profile.personality_traits && Array.isArray(profile.personality_traits)) {
        profile.personality_traits.forEach(traitObj => {
          const trait = typeof traitObj === 'string' ? traitObj : traitObj.trait;
          if (trait) {
            traitCounts[trait] = (traitCounts[trait] || 0) + 1;
          }
        });
      }
    });
    
    return Object.entries(traitCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([trait, count]) => ({ trait, count }));
  };

  const getCharacterEvolution = (profiles) => {
    if (profiles.length < 2) return { type: 'static', description: 'Character appears in only one chapter' };
    
    const firstProfile = profiles[0];
    const lastProfile = profiles[profiles.length - 1];
    
    // Extract trait names from new structure
    const getTraitNames = (traitArray) => {
      if (!Array.isArray(traitArray)) return [];
      return traitArray.map(t => typeof t === 'string' ? t : t.trait).filter(Boolean);
    };
    
    // Simple evolution detection based on trait changes
    const initialTraits = new Set(getTraitNames(firstProfile.personality_traits));
    const finalTraits = new Set(getTraitNames(lastProfile.personality_traits));
    
    const newTraits = [...finalTraits].filter(trait => !initialTraits.has(trait));
    const lostTraits = [...initialTraits].filter(trait => !finalTraits.has(trait));
    
    if (newTraits.length > lostTraits.length) {
      return { type: 'growth', description: `Developed new traits: ${newTraits.join(', ')}` };
    } else if (lostTraits.length > newTraits.length) {
      return { type: 'change', description: `Lost traits: ${lostTraits.join(', ')}` };
    } else {
      return { type: 'stable', description: 'Character traits remained relatively consistent' };
    }
  };

  // Process character profiles data
  const characters = useMemo(() => {
    if (!characterProfiles) return [];

    const characterMap = {};
    
    Object.entries(characterProfiles).forEach(([character, profiles]) => {
      characterMap[character] = {
        name: character,
        profiles: profiles.sort((a, b) => a.chapter_number - b.chapter_number),
        totalDialogues: profiles.reduce((sum, p) => sum + p.dialogue_count, 0),
        chaptersAppeared: profiles.length,
        firstAppearance: Math.min(...profiles.map(p => p.chapter_number)),
        lastAppearance: Math.max(...profiles.map(p => p.chapter_number)),
        // Get most common traits across all chapters
        commonTraits: getMostCommonTraits(profiles),
        // Get character evolution summary
        evolution: getCharacterEvolution(profiles)
      };
    });

    return Object.values(characterMap);
  }, [characterProfiles]);

  const getCharacterColor = (character) => {
    // Generate consistent colors for characters
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8E8'];
    const hash = character.name.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return colors[Math.abs(hash) % colors.length];
  };

  const renderCharacterOverview = () => {
    return (
      <Grid container spacing={3}>
        {characters.map((character) => (
          <Grid item xs={12} md={6} lg={4} key={character.name}>
            <Card 
              sx={{ 
                height: '100%',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
              onClick={() => {
                setSelectedCharacter(character.name);
                setViewMode('timeline');
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar 
                    sx={{ 
                      bgcolor: getCharacterColor(character),
                      mr: 2,
                      width: 48,
                      height: 48
                    }}
                  >
                    <PersonIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" component="div">
                      {character.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Chapters {character.firstAppearance}-{character.lastAppearance}
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      <DialogueIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                      {character.totalDialogues} dialogues
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      <TimelineIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                      {character.chaptersAppeared} chapters
                    </Typography>
                  </Box>
                  
                  <LinearProgress 
                    variant="determinate" 
                    value={(character.totalDialogues / Math.max(...characters.map(c => c.totalDialogues))) * 100}
                    sx={{ height: 6, borderRadius: 3 }}
                  />
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    <PsychologyIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                    Top Traits
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {character.commonTraits.slice(0, 3).map((trait, index) => (
                      <Chip
                        key={trait.trait}
                        label={trait.trait}
                        size="small"
                        color={index === 0 ? 'primary' : 'default'}
                        variant={index === 0 ? 'filled' : 'outlined'}
                      />
                    ))}
                  </Box>
                </Box>

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    <TrendingUpIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                    Character Arc
                  </Typography>
                  <Chip
                    label={character.evolution.type}
                    size="small"
                    color={
                      character.evolution.type === 'growth' ? 'success' :
                      character.evolution.type === 'change' ? 'warning' : 'default'
                    }
                  />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {character.evolution.description}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  const renderSelectedCharacterDetails = () => {
    const character = characters.find(c => c.name === selectedCharacter);
    if (!character) return null;

    return (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Avatar 
            sx={{ 
              bgcolor: getCharacterColor(character),
              mr: 2,
              width: 56,
              height: 56
            }}
          >
            <PersonIcon />
          </Avatar>
          <Box>
            <Typography variant="h4" component="h1">
              {character.name}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Character Development Analysis
            </Typography>
          </Box>
        </Box>

        <CharacterTimeline character={character} />
      </Box>
    );
  };

  if (!characterProfiles || Object.keys(characterProfiles).length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          No character profiles available
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Upload a dialogue index file with character analysis to see character development visualization.
        </Typography>
      </Paper>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Character Development Dashboard
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>View Mode</InputLabel>
              <Select
                value={viewMode}
                label="View Mode"
                onChange={(e) => setViewMode(e.target.value)}
              >
                <MenuItem value="overview">Characters Overview</MenuItem>
                <MenuItem value="timeline">Character Timeline</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          {viewMode === 'timeline' && (
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Select Character</InputLabel>
                <Select
                  value={selectedCharacter}
                  label="Select Character"
                  onChange={(e) => setSelectedCharacter(e.target.value)}
                >
                  {characters.map((character) => (
                    <MenuItem key={character.name} value={character.name}>
                      {character.name} ({character.chaptersAppeared} chapters)
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}
        </Grid>
      </Paper>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          Analyzing {characters.length} characters across {Math.max(...characters.map(c => c.lastAppearance))} chapters.
          Total dialogues: {characters.reduce((sum, c) => sum + c.totalDialogues, 0)}
        </Typography>
      </Alert>

      {viewMode === 'overview' && renderCharacterOverview()}
      {viewMode === 'timeline' && selectedCharacter && renderSelectedCharacterDetails()}
    </Box>
  );
};

export default CharacterDashboard;