import React from 'react';
import { Box, Typography, LinearProgress } from '@mui/material';

function Result({ prediction }) {
  const getColor = (probability) => {
    if (probability < 0.3) return 'success';
    if (probability < 0.7) return 'warning';
    return 'error';
  };

  const color = getColor(prediction.probability);

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6">Prédiction: {prediction.prediction}</Typography>
      <Typography variant="body1">
        Probabilité: {prediction.probability.toFixed(2)}
      </Typography>
      <LinearProgress
        variant="determinate"
        value={prediction.probability * 100}
        color={color}
        sx={{ mt: 1, height: 10, borderRadius: 5 }}
      />
    </Box>
  );
}

export default Result;
