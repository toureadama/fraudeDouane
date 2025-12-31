import React, { useState, useEffect } from 'react';
import { Button, TextField, Box, Typography, Grid, Select, MenuItem, FormControl, InputLabel } from '@mui/material';

function Form({ metadata, onSubmit, onReset }) {
  const [formData, setFormData] = useState({});

  useEffect(() => {
    if (!metadata) return;
    const init = Object.keys(metadata).reduce((acc, k) => ({ ...acc, [k]: '' }), {});
    setFormData(init);
  }, [metadata]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleReset = () => {
    const init = Object.keys(metadata || {}).reduce((acc, k) => ({ ...acc, [k]: '' }), {});
    setFormData(init);
    onReset();
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: '100%' }}>
      {Object.entries(metadata || {}).map(([key, values]) => (
        <Grid container spacing={2} alignItems="center" key={key}>
          <Grid item xs={4}>
            <Typography textAlign="left" sx={{ fontSize: '0.75rem' }}>{key}</Typography>
          </Grid>
          <Grid item xs={8}>
            {Array.isArray(values) && values.length > 0 ? (
              <FormControl fullWidth size="small" margin="dense">
                <InputLabel id={`${key}-label`} sx={{ fontSize: '0.75rem' }}>{/* label accessible */}</InputLabel>
                <Select
                  labelId={`${key}-label`}
                  name={key}
                  value={formData[key] ?? ''}
                  onChange={handleChange}
                  displayEmpty
                >
                  <MenuItem value="">
                    <em>--</em>
                  </MenuItem>
                  {values.map((v, i) => (
                    <MenuItem key={v ?? i} value={v}>{v}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            ) : (
              <TextField
                fullWidth
                margin="dense"
                name={key}
                value={formData[key] ?? ''}
                onChange={handleChange}
                required
                size="small"
              />
            )}
          </Grid>
        </Grid>
      ))}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
        <Button type="submit" variant="contained" color="primary">
          Soumettre
        </Button>
        <Button type="button" variant="outlined" color="secondary" onClick={handleReset}>
          Réinitialiser
        </Button>
      </Box>
    </Box>
  );
}

export default Form;
