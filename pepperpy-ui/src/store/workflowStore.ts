import axios from 'axios';
import { create } from 'zustand';

// Types
export interface Workflow {
  id: string;
  name: string;
  description: string;
  category?: string;
  type?: string;
  version?: string;
}

export interface WorkflowSchema {
  id: string;
  name: string;
  description: string;
  schema: any;
  version?: string;
}

export interface ExecutionResult {
  status: 'success' | 'error';
  workflow_id?: string;
  result?: any;
  error?: string;
  execution_time?: number;
  timestamp?: string;
  message?: string;
}

// Store interface
interface WorkflowState {
  // State
  workflows: Workflow[];
  isLoading: boolean;
  error: string | null;
  currentWorkflow: string | null;
  currentSchema: WorkflowSchema | null;
  inputData: string;
  configData: string;
  executionResult: ExecutionResult | null;
  
  // Actions
  fetchWorkflows: () => Promise<void>;
  fetchWorkflowSchema: (workflowId: string) => Promise<void>;
  setCurrentWorkflow: (workflowId: string | null) => void;
  updateInputData: (data: string) => void;
  updateConfigData: (data: string) => void;
  executeWorkflow: () => Promise<void>;
  resetExecutionResult: () => void;
}

// Create the store
const useWorkflowStore = create<WorkflowState>((set, get) => ({
  // Initial state
  workflows: [],
  isLoading: false,
  error: null,
  currentWorkflow: null,
  currentSchema: null,
  inputData: JSON.stringify({ "input": "Hello world" }, null, 2),
  configData: JSON.stringify({}, null, 2),
  executionResult: null,
  
  // Actions
  fetchWorkflows: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.get('/api/workflows');
      set({ workflows: response.data, isLoading: false });
    } catch (error: any) {
      console.error('Error fetching workflows:', error);
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to fetch workflows', 
        isLoading: false 
      });
    }
  },
  
  fetchWorkflowSchema: async (workflowId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.get(`/api/workflows/${workflowId}/schema`);
      set({ 
        currentSchema: response.data, 
        isLoading: false,
        // Set default input/config if available in schema
        inputData: JSON.stringify(response.data.schema?.example?.input_data || { "input": "Hello world" }, null, 2),
        configData: JSON.stringify(response.data.schema?.example?.config || {}, null, 2)
      });
    } catch (error: any) {
      console.error('Error fetching workflow schema:', error);
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to fetch workflow schema', 
        isLoading: false 
      });
    }
  },
  
  setCurrentWorkflow: (workflowId: string | null) => {
    set({ currentWorkflow: workflowId });
    if (workflowId) {
      get().fetchWorkflowSchema(workflowId);
    } else {
      set({ currentSchema: null });
    }
  },
  
  updateInputData: (data: string) => {
    set({ inputData: data });
  },
  
  updateConfigData: (data: string) => {
    set({ configData: data });
  },
  
  executeWorkflow: async () => {
    const { currentWorkflow, inputData, configData } = get();
    
    if (!currentWorkflow) {
      set({ error: 'No workflow selected' });
      return;
    }
    
    set({ isLoading: true, error: null });
    
    try {
      // Parse JSON data
      const parsedInput = JSON.parse(inputData);
      const parsedConfig = JSON.parse(configData);
      
      // Execute workflow
      const response = await axios.post(`/api/workflows/${currentWorkflow}/execute`, {
        input_data: parsedInput,
        config: parsedConfig
      });
      
      set({ 
        executionResult: response.data, 
        isLoading: false 
      });
    } catch (error: any) {
      console.error('Error executing workflow:', error);
      
      let errorMessage = error.message || 'Failed to execute workflow';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      set({ 
        executionResult: {
          status: 'error',
          message: errorMessage,
          timestamp: new Date().toISOString()
        },
        error: errorMessage,
        isLoading: false 
      });
    }
  },
  
  resetExecutionResult: () => {
    set({ executionResult: null });
  }
}));

export default useWorkflowStore; 