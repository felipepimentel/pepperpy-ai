import React, { useCallback, useEffect, useState } from 'react';
import useNotificationStore from '../store/notificationStore';
import useTodoStore from '../store/todoStore';
import TodoFilter from './TodoFilter';
import TodoHelp from './TodoHelp';

// Define Todo type
export interface Todo {
    id: string;
    title: string;
    description: string;
    completed: boolean;
    priority: 'low' | 'medium' | 'high';
    created_at: string;
}

// Todo component props
interface TodoProps {
    workflowId: string | null;
}

// Sort options for todos
type SortOption = 'created_desc' | 'created_asc' | 'priority_high' | 'priority_low' | 'alphabetical';

const Todo: React.FC<TodoProps> = ({ workflowId }) => {
    // Local state for form
    const [newTodo, setNewTodo] = useState<string>('');
    const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
    const [description, setDescription] = useState<string>('');
    const [showDescriptionInput, setShowDescriptionInput] = useState<boolean>(false);

    // Filter state
    const [priorityFilter, setPriorityFilter] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState<string>('');
    const [sortBy, setSortBy] = useState<SortOption>('created_desc');

    // Help dialog state
    const [showHelp, setShowHelp] = useState<boolean>(false);

    // Get todo state from store
    const {
        todos,
        isLoading,
        error,
        setCurrentWorkflow,
        fetchTodos,
        addTodo,
        toggleTodo,
        deleteTodo,
        clearCompletedTodos
    } = useTodoStore();

    // Get notification state
    const { showNotification } = useNotificationStore();

    // Set current workflow and fetch todos when workflowId changes
    useEffect(() => {
        setCurrentWorkflow(workflowId);
    }, [workflowId, setCurrentWorkflow]);

    // Handle adding a new todo
    const handleAddTodo = async () => {
        if (!newTodo.trim()) return;

        try {
            await addTodo(newTodo, priority, description);
            setNewTodo('');
            setDescription('');
            setShowDescriptionInput(false);
            showNotification('Todo added successfully', 'success');
        } catch (error) {
            showNotification('Failed to add todo', 'error');
        }
    };

    // Handle toggling a todo's completion status
    const handleToggleTodo = async (id: string) => {
        try {
            await toggleTodo(id);
        } catch (error) {
            showNotification('Failed to update todo', 'error');
        }
    };

    // Handle deleting a todo
    const handleDeleteTodo = async (id: string) => {
        try {
            await deleteTodo(id);
            showNotification('Todo deleted successfully', 'success');
        } catch (error) {
            showNotification('Failed to delete todo', 'error');
        }
    };

    // Handle clearing completed todos
    const handleClearCompleted = async () => {
        try {
            await clearCompletedTodos();
            showNotification('Completed tasks cleared successfully', 'success');
        } catch (error) {
            showNotification('Failed to clear completed tasks', 'error');
        }
    };

    // Toggle description input visibility
    const toggleDescriptionInput = () => {
        setShowDescriptionInput(!showDescriptionInput);
    };

    // Clear all filters
    const clearFilters = () => {
        setPriorityFilter(null);
        setStatusFilter(null);
        setSearchQuery('');
    };

    // Handle search input change
    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchQuery(e.target.value);
    };

    // Handle sort change
    const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSortBy(e.target.value as SortOption);
    };

    // Handle keyboard shortcuts
    const handleKeyDown = useCallback((e: KeyboardEvent) => {
        // Ignore when typing in an input or textarea
        if (
            document.activeElement?.tagName === 'INPUT' ||
            document.activeElement?.tagName === 'TEXTAREA'
        ) {
            return;
        }

        switch (e.key) {
            case '?':
                // Toggle help dialog
                setShowHelp(prev => !prev);
                break;

            case 'd':
                // Toggle description input (with Alt key)
                if (e.altKey) {
                    e.preventDefault();
                    toggleDescriptionInput();
                }
                break;

            case '1':
                // Filter by high priority (with Alt key)
                if (e.altKey) {
                    e.preventDefault();
                    setPriorityFilter(prev => prev === 'high' ? null : 'high');
                }
                break;

            case '2':
                // Filter by medium priority (with Alt key)
                if (e.altKey) {
                    e.preventDefault();
                    setPriorityFilter(prev => prev === 'medium' ? null : 'medium');
                }
                break;

            case '3':
                // Filter by low priority (with Alt key)
                if (e.altKey) {
                    e.preventDefault();
                    setPriorityFilter(prev => prev === 'low' ? null : 'low');
                }
                break;

            case 'c':
                // Toggle completed filter (with Alt key)
                if (e.altKey) {
                    e.preventDefault();
                    setStatusFilter(prev => {
                        if (prev === 'completed') return null;
                        if (prev === 'active') return 'completed';
                        return 'completed';
                    });
                }
                break;

            case 'a':
                // Toggle active filter (with Alt key)
                if (e.altKey) {
                    e.preventDefault();
                    setStatusFilter(prev => {
                        if (prev === 'active') return null;
                        if (prev === 'completed') return 'active';
                        return 'active';
                    });
                }
                break;

            case 'x':
                // Clear all filters (with Alt key)
                if (e.altKey) {
                    e.preventDefault();
                    clearFilters();
                }
                break;

            case 'f':
                // Focus search (with Alt key)
                if (e.altKey) {
                    e.preventDefault();
                    document.getElementById('todo-search')?.focus();
                }
                break;
        }
    }, []);

    // Add keyboard event listener
    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [handleKeyDown]);

    // Get color for priority
    const getPriorityColor = (priority: string): string => {
        switch (priority) {
            case 'high':
                return 'text-danger';
            case 'medium':
                return 'text-warning';
            case 'low':
                return 'text-success';
            default:
                return '';
        }
    };

    // Get priority weight for sorting
    const getPriorityWeight = (priority: string): number => {
        switch (priority) {
            case 'high': return 3;
            case 'medium': return 2;
            case 'low': return 1;
            default: return 0;
        }
    };

    // Filter todos based on current filters
    const filteredTodos = todos.filter(todo => {
        // Apply priority filter
        if (priorityFilter && todo.priority !== priorityFilter) {
            return false;
        }

        // Apply status filter
        if (statusFilter === 'completed' && !todo.completed) {
            return false;
        }

        if (statusFilter === 'active' && todo.completed) {
            return false;
        }

        // Apply search filter
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            const matchesTitle = todo.title.toLowerCase().includes(query);
            const matchesDescription = todo.description?.toLowerCase().includes(query) || false;
            if (!matchesTitle && !matchesDescription) {
                return false;
            }
        }

        return true;
    });

    // Sort filtered todos
    const sortedTodos = [...filteredTodos].sort((a, b) => {
        switch (sortBy) {
            case 'created_desc':
                return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            case 'created_asc':
                return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
            case 'priority_high':
                return getPriorityWeight(b.priority) - getPriorityWeight(a.priority);
            case 'priority_low':
                return getPriorityWeight(a.priority) - getPriorityWeight(b.priority);
            case 'alphabetical':
                return a.title.localeCompare(b.title);
            default:
                return 0;
        }
    });

    // Check if there are any completed todos
    const hasCompleted = todos.some(todo => todo.completed);

    // Render loading state
    if (isLoading && todos.length === 0) {
        return (
            <div className="p-4 text-center">
                <div className="animate-spin h-6 w-6 border-t-2 border-b-2 border-primary rounded-full mx-auto"></div>
                <p className="mt-2 text-sm text-secondary">Loading todos...</p>
            </div>
        );
    }

    // Render error state
    if (error && !isLoading && todos.length === 0) {
        return (
            <div className="p-4 bg-danger/5 text-danger rounded-md">
                <p className="font-medium mb-2">Failed to load todos</p>
                <p className="text-sm mb-3">{error}</p>
                <button
                    className="btn btn-secondary text-sm py-1.5 px-3"
                    onClick={fetchTodos}
                >
                    <i className="bi bi-arrow-clockwise me-1"></i> Retry
                </button>
            </div>
        );
    }

    return (
        <>
            <div className="card">
                <div className="card-header bg-primary text-white flex justify-between items-center">
                    <h3 className="font-medium">Task Manager</h3>
                    <div className="flex gap-2">
                        <button
                            className="text-white"
                            onClick={() => setShowHelp(true)}
                            title="Show help"
                        >
                            <i className="bi bi-question-circle"></i>
                        </button>
                        <button
                            className="text-white"
                            onClick={fetchTodos}
                            title="Refresh todos"
                        >
                            <i className="bi bi-arrow-clockwise"></i>
                        </button>
                    </div>
                </div>

                <div className="card-body">
                    {/* Add todo form */}
                    <div className="mb-4">
                        <div className="flex gap-2 mb-2">
                            <div className="flex-grow">
                                <input
                                    type="text"
                                    className="form-control"
                                    placeholder="Add a new task..."
                                    value={newTodo}
                                    onChange={(e) => setNewTodo(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && !showDescriptionInput && handleAddTodo()}
                                />
                            </div>
                            <div>
                                <select
                                    className="form-select"
                                    value={priority}
                                    onChange={(e) => setPriority(e.target.value as 'low' | 'medium' | 'high')}
                                >
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <div>
                                <button
                                    className="btn btn-secondary"
                                    onClick={toggleDescriptionInput}
                                    title={showDescriptionInput ? "Hide description" : "Add description"}
                                >
                                    <i className={`bi ${showDescriptionInput ? 'bi-dash' : 'bi-card-text'}`}></i>
                                </button>
                            </div>
                            <div>
                                <button
                                    className="btn btn-primary"
                                    onClick={handleAddTodo}
                                    disabled={isLoading || !newTodo.trim()}
                                >
                                    <i className="bi bi-plus"></i> Add
                                </button>
                            </div>
                        </div>

                        {showDescriptionInput && (
                            <div className="mb-2">
                                <textarea
                                    className="form-control"
                                    placeholder="Task description (optional)"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    rows={2}
                                ></textarea>
                            </div>
                        )}
                    </div>

                    {/* Search and sort controls */}
                    <div className="mb-4 flex flex-wrap gap-3">
                        <div className="relative flex-grow">
                            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                                <i className="bi bi-search text-gray-400"></i>
                            </div>
                            <input
                                id="todo-search"
                                type="search"
                                className="form-control pl-10"
                                placeholder="Search tasks by title or description..."
                                value={searchQuery}
                                onChange={handleSearchChange}
                            />
                            {searchQuery && (
                                <button
                                    className="absolute inset-y-0 right-0 flex items-center pr-3"
                                    onClick={() => setSearchQuery('')}
                                >
                                    <i className="bi bi-x-circle text-gray-400 hover:text-gray-600"></i>
                                </button>
                            )}
                        </div>

                        <div className="flex items-center min-w-[200px]">
                            <label htmlFor="sort-select" className="text-sm text-secondary whitespace-nowrap me-2">Sort by:</label>
                            <select
                                id="sort-select"
                                className="form-select text-sm"
                                value={sortBy}
                                onChange={handleSortChange}
                            >
                                <option value="created_desc">Newest first</option>
                                <option value="created_asc">Oldest first</option>
                                <option value="priority_high">Priority (high to low)</option>
                                <option value="priority_low">Priority (low to high)</option>
                                <option value="alphabetical">Alphabetical</option>
                            </select>
                        </div>
                    </div>

                    {/* Filters and actions */}
                    <div className="flex flex-wrap justify-between items-center mb-4">
                        <TodoFilter
                            priorityFilter={priorityFilter}
                            statusFilter={statusFilter}
                            onPriorityFilterChange={setPriorityFilter}
                            onStatusFilterChange={setStatusFilter}
                            clearFilters={clearFilters}
                        />

                        {hasCompleted && (
                            <button
                                className="btn btn-sm btn-danger ml-auto mt-2 sm:mt-0"
                                onClick={handleClearCompleted}
                                disabled={isLoading}
                            >
                                <i className="bi bi-trash me-1"></i> Clear Completed
                            </button>
                        )}
                    </div>

                    {/* Stats */}
                    <div className="flex justify-between mb-4 text-sm text-secondary">
                        <div>
                            <span className="font-semibold">{todos.length}</span> total tasks
                        </div>
                        <div>
                            <span className="font-semibold">{todos.filter(t => t.completed).length}</span> completed
                        </div>
                        <div>
                            <span className="font-semibold">{filteredTodos.length}</span> matching filters
                        </div>
                    </div>

                    {/* Todo list */}
                    <div className="todos-list">
                        {todos.length === 0 ? (
                            <p className="text-center text-secondary py-4">No tasks yet. Add one above!</p>
                        ) : filteredTodos.length === 0 ? (
                            <p className="text-center text-secondary py-4">No tasks match the current filters</p>
                        ) : (
                            sortedTodos.map(todo => (
                                <div
                                    key={todo.id}
                                    className={`
                      p-3 border-b last:border-b-0 flex items-center gap-2
                      ${todo.completed ? 'bg-gray-50' : ''}
                    `}
                                >
                                    <input
                                        type="checkbox"
                                        className="form-checkbox h-5 w-5 text-primary"
                                        checked={todo.completed}
                                        onChange={() => handleToggleTodo(todo.id)}
                                    />

                                    <div className="flex-grow">
                                        <p className={`font-medium ${todo.completed ? 'line-through text-secondary' : ''}`}>
                                            {todo.title}
                                        </p>
                                        {todo.description && (
                                            <p className="text-sm text-secondary mt-1">
                                                {todo.description}
                                            </p>
                                        )}
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <span className={`text-sm ${getPriorityColor(todo.priority)}`}>
                                            {todo.priority}
                                        </span>

                                        <button
                                            className="text-danger hover:text-danger-dark"
                                            onClick={() => handleDeleteTodo(todo.id)}
                                            title="Delete todo"
                                        >
                                            <i className="bi bi-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Keyboard shortcut hint */}
                    <div className="text-center mt-4 text-secondary text-xs">
                        Press <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">?</kbd> for keyboard shortcuts
                    </div>
                </div>
            </div>

            {/* Help dialog */}
            <TodoHelp isOpen={showHelp} onClose={() => setShowHelp(false)} />
        </>
    );
};

export default Todo; 