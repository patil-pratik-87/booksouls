import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Divider
} from '@mui/material';
import {
  Search as SearchIcon,
  Person as PersonIcon,
  Book as BookIcon,
  TheaterComedy as TheaterIcon,
  Refresh as RefreshIcon,
  Psychology as PsychologyIcon,
  FindInPage as FindInPageIcon,
  Group as GroupIcon
} from '@mui/icons-material';
import { API_ENDPOINTS, apiCall } from '../config/api';
import VectorResultDetail from './VectorResultDetail';

const VectorQueryInterface = () => {
  const [queryType, setQueryType] = useState('narrative');
  const [query, setQuery] = useState('');
  const [character, setCharacter] = useState('');
  const [chapterNumber, setChapterNumber] = useState('');
  const [theme, setTheme] = useState('');
  const [characterTraits, setCharacterTraits] = useState('');
  const [similarCharacter, setSimilarCharacter] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [isIndexerReady, setIsIndexerReady] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);

  // Initialize indexer when component mounts
  useEffect(() => {
    initializeIndexer();
  }, []);

  const initializeIndexer = async () => {
    try {
      setLoading(true);
      const data = await apiCall(API_ENDPOINTS.indexer.initialize, {
        method: 'POST'
      });

      setStats(data.stats);
      setIsIndexerReady(true);
    } catch (err) {
      setError(`Error connecting to indexer service: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const performQuery = async () => {
    if (!query.trim() && queryType !== 'character' && queryType !== 'chapter' && 
        queryType !== 'character_traits' && queryType !== 'similar_character') return;

    setLoading(true);
    setError(null);

    try {
      let body = { type: queryType };

      switch (queryType) {
        case 'narrative':
          body.query = query;
          break;
        case 'dialogue':
          body.query = query;
          break;
        case 'character':
          body.character = character;
          break;
        case 'chapter':
          body.chapter_number = parseInt(chapterNumber);
          break;
        case 'theme':
          body.theme = theme;
          break;
        case 'character_traits':
          body.query = characterTraits;
          body.type = 'character_profiles';
          break;
        case 'similar_character':
          body.query = `character personality like ${similarCharacter}`;
          body.type = 'character_profiles';
          break;
      }

      const data = await apiCall(API_ENDPOINTS.indexer.query, {
        method: 'POST',
        body: JSON.stringify(body)
      });

      setResults(data);
    } catch (err) {
      setError(`Query failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };


  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      performQuery();
    }
  };

  const renderQueryInput = () => {
    switch (queryType) {
      case 'narrative':
      case 'dialogue':
        return (
          <TextField
            fullWidth
            label={`Search ${queryType}`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Enter ${queryType} query...`}
            variant="outlined"
            multiline
            rows={2}
          />
        );
      case 'character':
        return (
          <TextField
            fullWidth
            label="Character Name"
            value={character}
            onChange={(e) => setCharacter(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter character name..."
            variant="outlined"
          />
        );
      case 'chapter':
        return (
          <TextField
            fullWidth
            label="Chapter Number"
            type="number"
            value={chapterNumber}
            onChange={(e) => setChapterNumber(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter chapter number..."
            variant="outlined"
          />
        );
      case 'theme':
        return (
          <TextField
            fullWidth
            label="Theme"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter theme to search..."
            variant="outlined"
          />
        );
      case 'character_traits':
        return (
          <TextField
            fullWidth
            label="Character Traits"
            value={characterTraits}
            onChange={(e) => setCharacterTraits(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter traits (e.g., brave, wise, conflicted)..."
            variant="outlined"
            multiline
            rows={2}
          />
        );
      case 'similar_character':
        return (
          <TextField
            fullWidth
            label="Character Name"
            value={similarCharacter}
            onChange={(e) => setSimilarCharacter(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter character name to find similar..."
            variant="outlined"
          />
        );
      default:
        return null;
    }
  };

  const handleResultClick = (id, document, metadata, similarity) => {
    setSelectedResult({
      document_id: id,
      content: document,
      metadata: metadata,
      similarity: similarity
    });
  };

  const renderResults = () => {
    if (!results || !results.results) return null;

    const { results: queryResults } = results;
    const ids = queryResults.ids?.[0] || [];
    console.log(queryResults);
    const documents = queryResults.documents?.[0] || [];
    const metadatas = queryResults.metadatas?.[0] || [];
    const distances = queryResults.distances?.[0] || [];

    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Results ({ids.length} found)
        </Typography>

        {ids.map((id, index) => {
          const similarity = distances[index] !== undefined ? 1 - distances[index] : 0;

          return (
            <Card
              key={id}
              sx={{
                mb: 2,
                cursor: 'pointer',
                '&:hover': {
                  bgcolor: 'action.hover',
                  boxShadow: 2
                }
              }}
              onClick={() => handleResultClick(id, documents[index], metadatas[index], similarity)}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, gap: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mr: 1 }}>
                    {id}
                  </Typography>
                  {distances[index] !== undefined && (
                    <Chip
                      label={`${(similarity * 100).toFixed(1)}%`}
                      size="small"
                      color="primary"
                      sx={{ mr: 1 }}
                    />
                  )}
                  {metadatas[index]?.character && (
                    <Chip
                      icon={<PersonIcon />}
                      label={metadatas[index].character}
                      size="small"
                    />
                  )}
                  {metadatas[index]?.semantic_type && (
                    <Chip
                      label={metadatas[index].semantic_type}
                      size="small"
                      variant="outlined"
                    />
                  )}
                  {metadatas[index]?.emotion && (
                    <Chip
                      label={metadatas[index].emotion}
                      size="small"
                      color="secondary"
                    />
                  )}

                  {metadatas[index]?.type && (
                    <Chip
                      label={metadatas[index].type}
                      size="small"
                      color="primary"
                    />
                  )}

                  {metadatas[index]?.personality_traits && (
                    <Chip
                      icon={<PsychologyIcon />}
                      label={metadatas[index].personality_traits.split(',')[0] + '...'}
                      size="small"
                      color="info"
                    />
                  )}

                  {metadatas[index]?.emotional_state && (
                    <Chip
                      label={`Mood: ${metadatas[index].emotional_state}`}
                      size="small"
                      color="secondary"
                      variant="outlined"
                    />
                  )}
                </Box>

                {documents[index] && (
                  <Typography variant="body2" sx={{
                    bgcolor: 'grey.50',
                    p: 1,
                    borderRadius: 1,
                    fontStyle: 'italic'
                  }}>
                    {documents[index].substring(0, 300)}
                    {documents[index].length > 300 && '...'}
                  </Typography>
                )}

                {metadatas[index] && (
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {metadatas[index].chapter_number && (
                      <Chip
                        icon={<BookIcon />}
                        label={`Chapter ${metadatas[index].chapter_number}`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    {metadatas[index].section_index && (
                      <Chip
                        label={`Section ${metadatas[index].section_index}`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          );
        })}
      </Box>
    );
  };

  if (!isIndexerReady) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress sx={{ mb: 2 }} />
        <Typography>Initializing Vector Indexer...</Typography>
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
            <Button
              onClick={initializeIndexer}
              sx={{ ml: 1 }}
              size="small"
              startIcon={<RefreshIcon />}
            >
              Retry
            </Button>
          </Alert>
        )}
      </Paper>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Vector Query Interface
      </Typography>

      {stats && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Indexer Ready:</strong> {stats.total_documents} documents indexed
            ({stats.narrative_store?.document_count || 0} narrative, {stats.dialogue_store?.document_count || 0} dialogue)
          </Typography>
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Query Type</InputLabel>
              <Select
                value={queryType}
                label="Query Type"
                onChange={(e) => setQueryType(e.target.value)}
              >
                <MenuItem value="narrative">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <BookIcon sx={{ mr: 1 }} />
                    Narrative Search
                  </Box>
                </MenuItem>
                <MenuItem value="dialogue">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TheaterIcon sx={{ mr: 1 }} />
                    Dialogue Search
                  </Box>
                </MenuItem>
                <MenuItem value="character">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <PersonIcon sx={{ mr: 1 }} />
                    Character Dialogues
                  </Box>
                </MenuItem>
                <MenuItem value="chapter">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <BookIcon sx={{ mr: 1 }} />
                    Chapter Content
                  </Box>
                </MenuItem>
                <MenuItem value="theme">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <SearchIcon sx={{ mr: 1 }} />
                    Theme Search
                  </Box>
                </MenuItem>
                <MenuItem value="character_traits">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <PsychologyIcon sx={{ mr: 1 }} />
                    Character Traits
                  </Box>
                </MenuItem>
                <MenuItem value="similar_character">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <GroupIcon sx={{ mr: 1 }} />
                    Similar Characters
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            {renderQueryInput()}
          </Grid>

          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="contained"
              onClick={performQuery}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
              sx={{ height: 56 }}
            >
              {loading ? 'Searching...' : 'Search'}
            </Button>
          </Grid>
        </Grid>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>

      {renderResults()}

      <VectorResultDetail
        result={selectedResult}
        onClose={() => setSelectedResult(null)}
      />
    </Box>
  );
};

export default VectorQueryInterface;