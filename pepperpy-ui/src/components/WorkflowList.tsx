import React from 'react';
import { Workflow } from '../store/workflowStore';

interface WorkflowListProps {
    workflows: Workflow[];
    currentWorkflow: string | null;
    isLoading: boolean;
    error: string | null;
    onSelect: (id: string) => void;
    onRefresh: () => void;
}

// Workflow type to icon mapping
const workflowIcons: Record<string, string> = {
    governance: 'shield-check',
    design: 'pencil-square',
    testing: 'bug',
    enhancement: 'gear',
    chat: 'chat-dots',
    default: 'diagram-3',
};

// Get icon for workflow
const getIcon = (type?: string): string => {
    const iconName = type && workflowIcons[type] ? workflowIcons[type] : workflowIcons.default;
    return `bi bi-${iconName}`;
};

const WorkflowList: React.FC<WorkflowListProps> = ({
    workflows,
    currentWorkflow,
    isLoading,
    error,
    onSelect,
    onRefresh,
}) => {
    if (isLoading) {
        return (
            <div className="p-4 text-center">
                <div className="animate-spin h-6 w-6 border-t-2 border-b-2 border-primary rounded-full mx-auto"></div>
                <p className="mt-2 text-sm text-secondary">Loading workflows...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-danger/5 text-danger rounded-md m-3">
                <p className="font-medium mb-2">Failed to load workflows</p>
                <p className="text-sm mb-3">{error}</p>
                <button
                    className="btn btn-secondary text-sm py-1.5 px-3"
                    onClick={onRefresh}
                >
                    <i className="bi bi-arrow-clockwise me-1"></i> Retry
                </button>
            </div>
        );
    }

    if (workflows.length === 0) {
        return (
            <div className="p-4 text-center text-secondary">
                <p>No workflows available</p>
                <button
                    className="btn btn-secondary text-sm py-1.5 px-3 mt-2"
                    onClick={onRefresh}
                >
                    <i className="bi bi-arrow-clockwise me-1"></i> Refresh
                </button>
            </div>
        );
    }

    // Group workflows by type
    const groupedWorkflows: Record<string, Workflow[]> = {};
    workflows.forEach(workflow => {
        const type = workflow.type || 'other';
        if (!groupedWorkflows[type]) {
            groupedWorkflows[type] = [];
        }
        groupedWorkflows[type].push(workflow);
    });

    // Sort workflow types
    const sortedTypes = Object.keys(groupedWorkflows).sort();

    return (
        <div className="px-3 py-2 h-full overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Workflows</h2>
                <button
                    className="text-secondary hover:text-primary"
                    onClick={onRefresh}
                    title="Refresh workflows"
                >
                    <i className="bi bi-arrow-clockwise"></i>
                </button>
            </div>

            {sortedTypes.map(type => (
                <div key={type} className="mb-4">
                    <h3 className="text-xs uppercase tracking-wider text-secondary font-semibold mb-2 px-2">
                        {type}
                    </h3>

                    {groupedWorkflows[type].map(workflow => (
                        <div
                            key={workflow.id}
                            className={`
                p-3 rounded-lg mb-2 cursor-pointer transition-all
                ${currentWorkflow === workflow.id
                                    ? 'bg-primary/10 border-l-4 border-primary'
                                    : 'bg-white hover:bg-gray-50 border-l-4 border-transparent'
                                }
              `}
                            onClick={() => onSelect(workflow.id)}
                        >
                            <div className="flex items-center gap-2 mb-1">
                                <i className={`${getIcon(workflow.type)} text-primary`}></i>
                                <h4 className="font-medium">{workflow.name}</h4>
                            </div>

                            <p className="text-sm text-secondary line-clamp-2">
                                {workflow.description || 'No description available'}
                            </p>

                            {workflow.type && (
                                <div className="mt-2">
                                    <span className={`badge badge-${workflow.type} || 'secondary'`}>
                                        {workflow.type}
                                    </span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
};

export default WorkflowList; 