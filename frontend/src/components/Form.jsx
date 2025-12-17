import React, { useState } from 'react';
import { Button, TextField, Box, Typography, Grid } from '@mui/material';

function Form({ metadata, onSubmit, onReset }) {
  const [formData, setFormData] = useState({
    CODE_DECLARANT: '',
    CODE_OPERATEUR: '',
    PROVENANCE: '',
    CODE_NATURE_COLIS: '',
    CODE_PORT_CHARG: '',
    IDEN_MOY_TRANSP_ARRIVE: '',
    COD_BANQUE: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleReset = () => {
    setFormData({
      CODE_DECLARANT: '',
      CODE_OPERATEUR: '',
      PROVENANCE: '',
      CODE_NATURE_COLIS: '',
      CODE_PORT_CHARG: '',
      IDEN_MOY_TRANSP_ARRIVE: '',
      COD_BANQUE: '',
    });
    onReset();
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: '100%' }}>
      {Object.entries(metadata).map(([key, values]) => (
        <Grid container spacing={2} alignItems="center" key={key}>
          <Grid item xs={4}>
            <Typography textAlign="left" sx={{ fontSize: '0.75rem' }}>{key}</Typography>
          </Grid>
          <Grid item xs={8}>
            <TextField
              fullWidth
              margin="dense"
              name={key}
              value={formData[key]}
              onChange={handleChange}
              required
              size="small"
            />
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
