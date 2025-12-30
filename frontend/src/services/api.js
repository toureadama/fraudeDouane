const API_URL = 'https://fraudedouane.onrender.com'; //render.com, 'http://localhost:8000'; // Update with your backend URL (http://127.0.0.1:8000/

export const fetchMetadata = async () => {
  const response = await fetch(`${API_URL}/metadata`);
  if (!response.ok) {
    throw new Error('Failed to fetch metadata');
  }
  return response.json();
};

export const fetchPrediction = async (formData) => {
  const response = await fetch(`${API_URL}/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(formData),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch prediction');
  }
  return response.json();
};
