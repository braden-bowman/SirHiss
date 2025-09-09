import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Alert,
  Paper,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  LinearProgress,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  Slider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  Add,
  Settings,
  PlayArrow,
  Stop,
  Delete,
  Edit,
  ExpandMore,
  Assessment,
  TrendingUp,
  Speed,
  Timeline,
  Psychology,
  GridOn,
  ShowChart,
  Analytics,
  Visibility,
  VisibilityOff,
  SmartToy,
} from '@mui/icons-material';

// Algorithm types and their display information
const ALGORITHM_TYPES = {
  'AdvancedTechnicalIndicator': {
    name: 'Technical Analysis',
    description: 'RSI, MACD, Bollinger Bands with advanced indicators',
    icon: <Analytics />,
    color: '#1976d2',
    category: 'Technical Analysis',
    difficulty: 'Intermediate',
  },
  'Scalping': {
    name: 'Scalping',
    description: 'High-frequency trading on micro-movements',
    icon: <Speed />,
    color: '#d32f2f',
    category: 'High Frequency',
    difficulty: 'Advanced',
  },
  'DynamicDCA': {
    name: 'Dollar Cost Averaging',
    description: 'Systematic buying with volatility adjustments',
    icon: <Timeline />,
    color: '#388e3c',
    category: 'Long-term Investment',
    difficulty: 'Beginner',
  },
  'GridTrading': {
    name: 'Grid Trading',
    description: 'Automated buy/sell orders at regular intervals',
    icon: <GridOn />,
    color: '#f57c00',
    category: 'Market Making',
    difficulty: 'Intermediate',
  },
  'TrendFollowing': {
    name: 'Trend Following',
    description: 'Moving averages and ATR-based trend trading',
    icon: <TrendingUp />,
    color: '#7b1fa2',
    category: 'Trend Following',
    difficulty: 'Intermediate',
  },
  'Sentiment': {
    name: 'Sentiment Trading',
    description: 'News and social media sentiment analysis',
    icon: <Psychology />,
    color: '#0288d1',
    category: 'Sentiment Analysis',
    difficulty: 'Advanced',
  },
  'Arbitrage': {
    name: 'Statistical Arbitrage',
    description: 'Mean reversion and statistical patterns',
    icon: <ShowChart />,
    color: '#5d4037',
    category: 'Statistical Arbitrage',
    difficulty: 'Advanced',
  },
};

interface AlgorithmConfig {
  id: number;
  algorithm_type: string;
  algorithm_name: string;
  position_size: number;
  max_position_size: number;
  stop_loss: number;
  take_profit: number;
  risk_per_trade: number;
  enabled: boolean;
  parameters: Record<string, any>;
  total_trades: number;
  winning_trades: number;
  win_rate: number;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  created_at: string;
  updated_at: string;
}

interface AlgorithmTemplate {
  id: number;
  name: string;
  algorithm_type: string;
  description: string;
  category: string;
  default_position_size: number;
  default_parameters: Record<string, any>;
  difficulty_level: string;
  min_capital: number;
  recommended_timeframe: string;
}

interface AlgorithmManagerProps {
  botId: number;
  onAlgorithmsChange?: () => void;
}

export function AlgorithmManager({ botId, onAlgorithmsChange }: AlgorithmManagerProps) {
  const [algorithms, setAlgorithms] = useState<AlgorithmConfig[]>([]);
  const [templates, setTemplates] = useState<AlgorithmTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [parametersDialogOpen, setParametersDialogOpen] = useState(false);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<AlgorithmConfig | null>(null);
  const [algorithmParameters, setAlgorithmParameters] = useState<Record<string, any>>({});
  const [activeTab, setActiveTab] = useState(0);

  const [newAlgorithm, setNewAlgorithm] = useState({
    algorithm_name: '',
    algorithm_type: '',
    position_size: 0.1,
    template_id: null as number | null,
  });

  useEffect(() => {
    loadAlgorithms();
    loadTemplates();
  }, [botId]);

  const loadAlgorithms = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/algorithms/bots/${botId}/algorithms`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAlgorithms(data);
      } else {
        setError('Failed to load algorithms');
      }
    } catch (err) {
      setError('Error loading algorithms');
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/v1/algorithms/templates', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (err) {
      console.error('Error loading templates:', err);
    }
  };

  const createAlgorithm = async () => {
    try {
      let endpoint = `/api/v1/algorithms/bots/${botId}/algorithms`;
      let payload: any = {
        algorithm_type: newAlgorithm.algorithm_type,
        algorithm_name: newAlgorithm.algorithm_name,
        position_size: newAlgorithm.position_size,
      };

      if (newAlgorithm.template_id) {
        endpoint = `/api/v1/algorithms/bots/${botId}/algorithms/from-template/${newAlgorithm.template_id}`;
        payload = {
          algorithm_name: newAlgorithm.algorithm_name,
          position_size: newAlgorithm.position_size,
        };
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setCreateDialogOpen(false);
        setNewAlgorithm({
          algorithm_name: '',
          algorithm_type: '',
          position_size: 0.1,
          template_id: null,
        });
        loadAlgorithms();
        onAlgorithmsChange?.();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create algorithm');
      }
    } catch (err) {
      setError('Error creating algorithm');
    }
  };

  const toggleAlgorithm = async (algorithmId: number) => {
    try {
      const response = await fetch(`/api/v1/algorithms/algorithms/${algorithmId}/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        loadAlgorithms();
        onAlgorithmsChange?.();
      }
    } catch (err) {
      setError('Error toggling algorithm');
    }
  };

  const deleteAlgorithm = async (algorithmId: number) => {
    try {
      const response = await fetch(`/api/v1/algorithms/algorithms/${algorithmId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        loadAlgorithms();
        onAlgorithmsChange?.();
      }
    } catch (err) {
      setError('Error deleting algorithm');
    }
  };

  const openParametersDialog = async (algorithm: AlgorithmConfig) => {
    try {
      setSelectedAlgorithm(algorithm);
      
      const response = await fetch(`/api/v1/algorithms/algorithms/${algorithm.id}/parameters`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const parameters = await response.json();
        setAlgorithmParameters(parameters);
        setParametersDialogOpen(true);
      }
    } catch (err) {
      setError('Error loading algorithm parameters');
    }
  };

  const updateParameters = async () => {
    if (!selectedAlgorithm) return;

    try {
      const updatedParams = Object.keys(algorithmParameters).reduce((acc, key) => {
        acc[key] = algorithmParameters[key].value;
        return acc;
      }, {} as Record<string, any>);

      const response = await fetch(`/api/v1/algorithms/algorithms/${selectedAlgorithm.id}/parameters`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedParams),
      });

      if (response.ok) {
        setParametersDialogOpen(false);
        loadAlgorithms();
        onAlgorithmsChange?.();
      }
    } catch (err) {
      setError('Error updating parameters');
    }
  };

  const formatNumber = (value: number, decimals = 2) => {
    return value?.toFixed(decimals) || '0.00';
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'beginner': return '#4caf50';
      case 'intermediate': return '#ff9800';
      case 'advanced': return '#f44336';
      case 'expert': return '#3f51b5';
      default: return '#9e9e9e';
    }
  };

  const renderAlgorithmCard = (algorithm: AlgorithmConfig) => {
    const typeInfo = ALGORITHM_TYPES[algorithm.algorithm_type as keyof typeof ALGORITHM_TYPES] || {
      name: algorithm.algorithm_type,
      description: 'Custom algorithm',
      icon: <Settings />,
      color: '#9e9e9e',
    };

    return (
      <Card key={algorithm.id} sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ 
                p: 1, 
                borderRadius: 2, 
                backgroundColor: `${typeInfo.color}20`,
                color: typeInfo.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {typeInfo.icon}
              </Box>
              <Box>
                <Typography variant="h6" component="div">
                  {algorithm.algorithm_name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {typeInfo.name}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Switch
                checked={algorithm.enabled}
                onChange={() => toggleAlgorithm(algorithm.id)}
                size="small"
              />
              <Chip
                label={algorithm.enabled ? 'Active' : 'Inactive'}
                color={algorithm.enabled ? 'success' : 'default'}
                size="small"
              />
            </Box>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">Configuration</Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Position Size" 
                    secondary={`${(algorithm.position_size * 100).toFixed(1)}%`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Stop Loss" 
                    secondary={`${(algorithm.stop_loss * 100).toFixed(1)}%`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Take Profit" 
                    secondary={`${(algorithm.take_profit * 100).toFixed(1)}%`}
                  />
                </ListItem>
              </List>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">Performance</Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="Total Trades" 
                    secondary={algorithm.total_trades}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Win Rate" 
                    secondary={`${(algorithm.win_rate * 100).toFixed(1)}%`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Total Return" 
                    secondary={
                      <Typography 
                        color={algorithm.total_return >= 0 ? 'success.main' : 'error.main'}
                        variant="body2"
                      >
                        {algorithm.total_return >= 0 ? '+' : ''}{formatNumber(algorithm.total_return)}%
                      </Typography>
                    }
                  />
                </ListItem>
              </List>
            </Grid>
          </Grid>
        </CardContent>
        <CardActions>
          <Button
            size="small"
            startIcon={<Settings />}
            onClick={() => openParametersDialog(algorithm)}
          >
            Configure
          </Button>
          <Button
            size="small"
            startIcon={<Assessment />}
          >
            Analytics
          </Button>
          <Button
            size="small"
            startIcon={<Delete />}
            color="error"
            onClick={() => deleteAlgorithm(algorithm.id)}
          >
            Delete
          </Button>
        </CardActions>
      </Card>
    );
  };

  const renderTemplateCard = (template: AlgorithmTemplate) => {
    const typeInfo = ALGORITHM_TYPES[template.algorithm_type as keyof typeof ALGORITHM_TYPES];
    
    return (
      <Card key={template.id} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Box sx={{ 
              p: 1, 
              borderRadius: 2, 
              backgroundColor: `${typeInfo?.color || '#9e9e9e'}20`,
              color: typeInfo?.color || '#9e9e9e',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {typeInfo?.icon || <Settings />}
            </Box>
            <Box>
              <Typography variant="h6" component="div">
                {template.name}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                <Chip 
                  label={template.category} 
                  size="small" 
                  variant="outlined"
                />
                <Chip 
                  label={template.difficulty_level} 
                  size="small" 
                  sx={{ 
                    backgroundColor: getDifficultyColor(template.difficulty_level),
                    color: 'white'
                  }}
                />
              </Box>
            </Box>
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {template.description}
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
              Min. Capital: ${template.min_capital.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Timeframe: {template.recommended_timeframe}
            </Typography>
          </Box>
        </CardContent>
        <CardActions>
          <Button
            variant="contained"
            fullWidth
            onClick={() => {
              setNewAlgorithm(prev => ({
                ...prev,
                algorithm_type: template.algorithm_type,
                template_id: template.id,
                position_size: template.default_position_size,
              }));
              setCreateDialogOpen(true);
            }}
          >
            Use Template
          </Button>
        </CardActions>
      </Card>
    );
  };

  const renderParameterField = (key: string, paramInfo: any) => {
    const { value, description, type, min, max, step } = paramInfo;

    if (type === 'boolean') {
      return (
        <Box key={key} sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {description}
              </Typography>
            </Box>
            <Switch
              checked={value}
              onChange={(e) => setAlgorithmParameters(prev => ({
                ...prev,
                [key]: { ...prev[key], value: e.target.checked }
              }))}
            />
          </Box>
        </Box>
      );
    }

    if (type === 'number' || type === 'integer') {
      return (
        <Box key={key} sx={{ mb: 3 }}>
          <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 1 }}>
            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {description}
          </Typography>
          <Box sx={{ px: 2 }}>
            <Slider
              value={value}
              min={min}
              max={max}
              step={step || (type === 'integer' ? 1 : 0.01)}
              onChange={(_, newValue) => setAlgorithmParameters(prev => ({
                ...prev,
                [key]: { ...prev[key], value: newValue }
              }))}
              valueLabelDisplay="auto"
              marks={min !== undefined && max !== undefined && (max - min) <= 10 ? 
                Array.from({ length: Math.floor((max - min) / (step || 1)) + 1 }, (_, i) => ({
                  value: min + i * (step || 1),
                  label: (min + i * (step || 1)).toString()
                })) : undefined
              }
            />
          </Box>
          <TextField
            size="small"
            type="number"
            value={value}
            onChange={(e) => setAlgorithmParameters(prev => ({
              ...prev,
              [key]: { ...prev[key], value: parseFloat(e.target.value) }
            }))}
            inputProps={{ min, max, step: step || (type === 'integer' ? 1 : 0.01) }}
            sx={{ mt: 1, width: 120 }}
          />
        </Box>
      );
    }

    return null;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          <Tab label={`Active Algorithms (${algorithms.length})`} />
          <Tab label="Algorithm Templates" />
        </Tabs>
      </Box>

      {activeTab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">Algorithm Configurations</Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Add Algorithm
            </Button>
          </Box>

          {algorithms.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <SmartToy sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No algorithms configured
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Add your first algorithm to start automated trading
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => setCreateDialogOpen(true)}
              >
                Add Algorithm
              </Button>
            </Paper>
          ) : (
            algorithms.map(renderAlgorithmCard)
          )}
        </Box>
      )}

      {activeTab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Algorithm Templates
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip label="Enhanced AI Strategies Available" color="primary" variant="outlined" />
              <Chip label={`${templates.length} Templates`} size="small" />
            </Box>
          </Box>
          <Grid container spacing={3}>
            {templates.map((template) => (
              <Grid item xs={12} md={6} lg={4} key={template.id}>
                {renderTemplateCard(template)}
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Create Algorithm Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Algorithm</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Algorithm Name"
              value={newAlgorithm.algorithm_name}
              onChange={(e) => setNewAlgorithm(prev => ({ ...prev, algorithm_name: e.target.value }))}
              margin="normal"
            />
            
            {!newAlgorithm.template_id && (
              <FormControl fullWidth margin="normal">
                <InputLabel>Algorithm Type</InputLabel>
                <Select
                  value={newAlgorithm.algorithm_type}
                  onChange={(e) => setNewAlgorithm(prev => ({ ...prev, algorithm_type: e.target.value }))}
                >
                  {Object.entries(ALGORITHM_TYPES).map(([key, info]) => (
                    <MenuItem key={key} value={key}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {info.icon}
                        {info.name}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            
            <TextField
              fullWidth
              label="Position Size (%)"
              type="number"
              value={newAlgorithm.position_size * 100}
              onChange={(e) => setNewAlgorithm(prev => ({ ...prev, position_size: parseFloat(e.target.value) / 100 }))}
              margin="normal"
              inputProps={{ min: 1, max: 100, step: 0.1 }}
              helperText="Percentage of portfolio to allocate to this algorithm"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={createAlgorithm} 
            variant="contained"
            disabled={!newAlgorithm.algorithm_name || (!newAlgorithm.template_id && !newAlgorithm.algorithm_type)}
          >
            Create Algorithm
          </Button>
        </DialogActions>
      </Dialog>

      {/* Parameters Dialog */}
      <Dialog open={parametersDialogOpen} onClose={() => setParametersDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedAlgorithm && `Configure ${selectedAlgorithm.algorithm_name}`}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {Object.entries(algorithmParameters).map(([key, paramInfo]) => 
              renderParameterField(key, paramInfo)
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setParametersDialogOpen(false)}>Cancel</Button>
          <Button onClick={updateParameters} variant="contained">
            Update Parameters
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}