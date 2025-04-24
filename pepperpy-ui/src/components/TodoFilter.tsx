import React from 'react';

interface TodoFilterProps {
  priorityFilter: string | null;
  statusFilter: string | null;
  onPriorityFilterChange: (priority: string | null) => void;
  onStatusFilterChange: (status: string | null) => void;
  clearFilters: () => void;
}

const TodoFilter: React.FC<TodoFilterProps> = ({
  priorityFilter,
  statusFilter,
  onPriorityFilterChange,
  onStatusFilterChange,
  clearFilters
}) => {
  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <div className="flex items-center">
        <span className="text-sm text-secondary me-2">Priority:</span>
        <div className="btn-group btn-group-sm">
          <button
            className={`btn btn-sm ${priorityFilter === 'high' ? 'btn-danger' : 'btn-secondary'}`}
            onClick={() => onPriorityFilterChange(priorityFilter === 'high' ? null : 'high')}
          >
            High
          </button>
          <button
            className={`btn btn-sm ${priorityFilter === 'medium' ? 'btn-warning' : 'btn-secondary'}`}
            onClick={() => onPriorityFilterChange(priorityFilter === 'medium' ? null : 'medium')}
          >
            Medium
          </button>
          <button
            className={`btn btn-sm ${priorityFilter === 'low' ? 'btn-success' : 'btn-secondary'}`}
            onClick={() => onPriorityFilterChange(priorityFilter === 'low' ? null : 'low')}
          >
            Low
          </button>
        </div>
      </div>

      <div className="flex items-center">
        <span className="text-sm text-secondary me-2">Status:</span>
        <div className="btn-group btn-group-sm">
          <button
            className={`btn btn-sm ${statusFilter === 'completed' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => onStatusFilterChange(statusFilter === 'completed' ? null : 'completed')}
          >
            Completed
          </button>
          <button
            className={`btn btn-sm ${statusFilter === 'active' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => onStatusFilterChange(statusFilter === 'active' ? null : 'active')}
          >
            Active
          </button>
        </div>
      </div>

      {(priorityFilter || statusFilter) && (
        <button
          className="btn btn-sm btn-secondary"
          onClick={clearFilters}
        >
          <i className="bi bi-x me-1"></i> Clear Filters
        </button>
      )}
    </div>
  );
};

export default TodoFilter; 