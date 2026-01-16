/**
 * API Service for communicating with backend
 */
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Design API
export const createDesign = async (designData) => {
  const response = await apiClient.post('/api/design/', designData);
  return response.data;
};

export const getDesign = async (designId) => {
  const response = await apiClient.get(`/api/design/${designId}`);
  return response.data;
};

export const listDesigns = async () => {
  const response = await apiClient.get('/api/design/');
  return response.data;
};

// Simulation API
export const runSimulation = async (simulationData) => {
  const response = await apiClient.post('/api/simulation/run', simulationData);
  return response.data;
};

export const getSimulation = async (simulationId) => {
  const response = await apiClient.get(`/api/simulation/${simulationId}`);
  return response.data;
};

// Vendor API
export const matchVendors = async (vendorData) => {
  const response = await apiClient.post('/api/vendor/match', vendorData);
  return response.data;
};

export default apiClient;
