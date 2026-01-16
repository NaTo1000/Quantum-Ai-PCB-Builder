import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Schematic API
export const generateSchematic = async (
  prompt: string,
  designType: string = 'pcb',
  outputFormat: string = 'rtl'
) => {
  const response = await api.post('/api/schematic/generate', {
    prompt,
    design_type: designType,
    output_format: outputFormat,
  });
  return response.data;
};

export const getSchematic = async (schematicId: string) => {
  const response = await api.get(`/api/schematic/${schematicId}`);
  return response.data;
};

// Design Checks API
export const runDesignChecks = async (
  schematicId: string,
  checkTypes: string[] = ['drc', 'lvs', 'thermal', 'signal_integrity']
) => {
  const response = await api.post('/api/checks/run', {
    schematic_id: schematicId,
    check_types: checkTypes,
  });
  return response.data;
};

// Simulation API
export const runSimulation = async (
  schematicId: string,
  simulationType: string = 'spice',
  parameters: Record<string, any> = {}
) => {
  const response = await api.post('/api/simulation/run', {
    schematic_id: schematicId,
    simulation_type: simulationType,
    parameters,
  });
  return response.data;
};

// Components API
export const generateBOM = async (schematicId: string) => {
  const response = await api.post(`/api/components/bom/${schematicId}`);
  return response.data;
};

export const generateComponentDrawing = async (componentId: string) => {
  const response = await api.post('/api/components/drawing', {
    component_id: componentId,
  });
  return response.data;
};

// Vendors API
export const matchVendors = async (
  schematicId: string,
  quantity: number = 1000,
  preferredLocations: string[] = []
) => {
  const response = await api.post('/api/vendors/match', {
    schematic_id: schematicId,
    quantity,
    preferred_locations: preferredLocations,
  });
  return response.data;
};

export const listVendors = async (vendorType?: string) => {
  const params = vendorType ? { vendor_type: vendorType } : {};
  const response = await api.get('/api/vendors/', { params });
  return response.data;
};

export default api;
