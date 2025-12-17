import React, { useState, useEffect } from 'react';
import { Container, Typography, CircularProgress, Alert } from '@mui/material';
import Form from './components/Form';
import Result from './components/Result';
import { fetchMetadata, fetchPrediction } from './services/api';

function App() {
  const [metadata, setMetadata] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const data = await fetchMetadata();
        setMetadata(data);
      } catch (err) {
        setError("Failed to load metadata. Please try again later.");
      }
    };
    loadMetadata();
  }, []);

  const handleSubmit = async (formData) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchPrediction(formData);
      setPrediction(result);
    } catch (err) {
      setError("Failed to get prediction. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPrediction(null);
    setError(null);
  };

  return (
    <Container maxWidth="sm">
      <Typography variant="h4" component="h1" gutterBottom>
        Détection de Fraude Douanière
      </Typography>
      {error && <Alert severity="error">{error}</Alert>}
      {metadata ? (
        <>
          <Form metadata={metadata} onSubmit={handleSubmit} onReset={handleReset} />
          {loading && <CircularProgress />}
          {prediction && <Result prediction={prediction} />}
        </>
      ) : (
        <CircularProgress />
      )}
    </Container>
  );
}

export default App;
