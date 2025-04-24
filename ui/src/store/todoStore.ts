import axios from 'axios';
import { create } from 'zustand';
import { Todo } from '../components/Todo';

interface TodoState {
  // State
  todos: Todo[];
  isLoading: boolean;
  error: string | null;
  currentWorkflowId: string | null;
  
  // Actions
  setCurrentWorkflow: (workflowId: string | null) => void;
  fetchTodos: () => Promise<void>;
  addTodo: (title: string, priority: 'low' | 'medium' | 'high', description?: string) => Promise<void>;
  toggleTodo: (id: string) => Promise<void>;
  deleteTodo: (id: string) => Promise<void>;
  clearTodos: () => void;
  clearCompletedTodos: () => Promise<void>;
}

const useTodoStore = create<TodoState>((set, get) => ({
  // Initial state
  todos: [],
  isLoading: false,
  error: null,
  currentWorkflowId: null,
  
  // Set current workflow
  setCurrentWorkflow: (workflowId: string | null) => {
    set({ currentWorkflowId: workflowId });
    
    // Clear todos when workflow changes
    set({ todos: [] });
    
    // Fetch todos if we have a workflow ID
    if (workflowId) {
      get().fetchTodos();
    }
  },
  
  // Fetch todos for current workflow
  fetchTodos: async () => {
    const { currentWorkflowId } = get();
    if (!currentWorkflowId) return;
    
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.get(`/api/workflows/${currentWorkflowId}/todos`);
      set({ todos: response.data, isLoading: false });
    } catch (error: any) {
      console.error('Error fetching todos:', error);
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to fetch todos', 
        isLoading: false 
      });
    }
  },
  
  // Add a new todo
  addTodo: async (title: string, priority: 'low' | 'medium' | 'high', description?: string) => {
    const { currentWorkflowId, todos } = get();
    if (!currentWorkflowId || !title.trim()) return;
    
    set({ isLoading: true });
    
    try {
      const response = await axios.post(`/api/workflows/${currentWorkflowId}/todos`, {
        title,
        priority,
        description,
        completed: false
      });
      
      set({ 
        todos: [...todos, response.data],
        isLoading: false 
      });
    } catch (error: any) {
      console.error('Error adding todo:', error);
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to add todo', 
        isLoading: false 
      });
    }
  },
  
  // Toggle todo completion status
  toggleTodo: async (id: string) => {
    const { currentWorkflowId, todos } = get();
    if (!currentWorkflowId) return;
    
    const todoToUpdate = todos.find(todo => todo.id === id);
    if (!todoToUpdate) return;
    
    try {
      const response = await axios.patch(`/api/workflows/${currentWorkflowId}/todos/${id}`, {
        completed: !todoToUpdate.completed
      });
      
      set({ 
        todos: todos.map(todo => todo.id === id ? response.data : todo)
      });
    } catch (error: any) {
      console.error('Error updating todo:', error);
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to update todo'
      });
    }
  },
  
  // Delete a todo
  deleteTodo: async (id: string) => {
    const { currentWorkflowId, todos } = get();
    if (!currentWorkflowId) return;
    
    try {
      await axios.delete(`/api/workflows/${currentWorkflowId}/todos/${id}`);
      
      set({ 
        todos: todos.filter(todo => todo.id !== id)
      });
    } catch (error: any) {
      console.error('Error deleting todo:', error);
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to delete todo'
      });
    }
  },
  
  // Clear all todos
  clearTodos: () => {
    set({ todos: [] });
  },
  
  // Clear all completed todos
  clearCompletedTodos: async () => {
    const { currentWorkflowId, todos } = get();
    if (!currentWorkflowId) return;
    
    // Get all completed todos
    const completedTodos = todos.filter(todo => todo.completed);
    if (completedTodos.length === 0) return;
    
    set({ isLoading: true });
    
    try {
      // Delete each completed todo
      for (const todo of completedTodos) {
        await axios.delete(`/api/workflows/${currentWorkflowId}/todos/${todo.id}`);
      }
      
      // Update state by removing completed todos
      set({ 
        todos: todos.filter(todo => !todo.completed),
        isLoading: false
      });
    } catch (error: any) {
      console.error('Error clearing completed todos:', error);
      set({ 
        error: error.response?.data?.detail || error.message || 'Failed to clear completed todos',
        isLoading: false
      });
      
      // Refresh the list to ensure it's in sync
      get().fetchTodos();
    }
  }
}));

export default useTodoStore; 