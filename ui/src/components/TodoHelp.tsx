import React from 'react';

interface TodoHelpProps {
    isOpen: boolean;
    onClose: () => void;
}

const TodoHelp: React.FC<TodoHelpProps> = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <div className="p-5">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold">Task Manager Help</h2>
                        <button
                            className="text-gray-500 hover:text-gray-700"
                            onClick={onClose}
                        >
                            <i className="bi bi-x-lg"></i>
                        </button>
                    </div>

                    <div className="mb-6">
                        <h3 className="font-semibold text-lg mb-2">Keyboard Shortcuts</h3>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                            <div className="py-1">
                                <span className="font-medium">Add task:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">Enter</kbd>
                            </div>
                            <div className="py-1">
                                <span className="font-medium">Add description:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">Alt</kbd> + <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">D</kbd>
                            </div>
                            <div className="py-1">
                                <span className="font-medium">Focus search:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">Alt</kbd> + <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">F</kbd>
                            </div>
                            <div className="py-1">
                                <span className="font-medium">Toggle help:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">?</kbd>
                            </div>
                            <div className="py-1">
                                <span className="font-medium">Filter by high priority:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">Alt</kbd> + <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">1</kbd>
                            </div>
                            <div className="py-1">
                                <span className="font-medium">Filter by medium priority:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">Alt</kbd> + <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">2</kbd>
                            </div>
                            <div className="py-1">
                                <span className="font-medium">Filter by low priority:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">Alt</kbd> + <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">3</kbd>
                            </div>
                            <div className="py-1">
                                <span className="font-medium">Filter completed tasks:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">Alt</kbd> + <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">C</kbd>
                            </div>
                            <div className="py-1">
                                <span className="font-medium">Filter active tasks:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">Alt</kbd> + <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">A</kbd>
                            </div>
                            <div className="py-1">
                                <span className="font-medium">Clear all filters:</span> <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">Alt</kbd> + <kbd className="px-1 py-0.5 rounded bg-gray-100 border text-xs">X</kbd>
                            </div>
                        </div>
                    </div>

                    <div className="mb-6">
                        <h3 className="font-semibold text-lg mb-2">Task Priorities</h3>
                        <div className="flex flex-col gap-2 text-sm">
                            <div className="flex items-center">
                                <span className="w-16 text-danger font-medium">High</span>
                                <span>Critical tasks that need immediate attention</span>
                            </div>
                            <div className="flex items-center">
                                <span className="w-16 text-warning font-medium">Medium</span>
                                <span>Important tasks to complete soon</span>
                            </div>
                            <div className="flex items-center">
                                <span className="w-16 text-success font-medium">Low</span>
                                <span>Tasks that can be addressed later</span>
                            </div>
                        </div>
                    </div>

                    <div className="mb-6">
                        <h3 className="font-semibold text-lg mb-2">Filtering & Sorting</h3>
                        <div className="text-sm space-y-2">
                            <p>
                                <span className="font-medium">Filters:</span> You can filter tasks by priority (High, Medium, Low) and status (Active, Completed). Use the filter buttons or keyboard shortcuts to toggle filters quickly.
                            </p>
                            <p>
                                <span className="font-medium">Search:</span> Use the search box to filter tasks by title or description text.
                            </p>
                            <p>
                                <span className="font-medium">Sorting:</span> Change the order of tasks using the sort dropdown:
                            </p>
                            <ul className="list-disc list-inside pl-4 space-y-1">
                                <li><span className="font-medium">Newest first:</span> Most recently created tasks at the top</li>
                                <li><span className="font-medium">Oldest first:</span> Oldest tasks at the top</li>
                                <li><span className="font-medium">Priority (high to low):</span> Tasks sorted by highest priority first</li>
                                <li><span className="font-medium">Priority (low to high):</span> Tasks sorted by lowest priority first</li>
                                <li><span className="font-medium">Alphabetical:</span> Tasks sorted by title alphabetically</li>
                            </ul>
                        </div>
                    </div>

                    <div className="text-center mt-6">
                        <button
                            className="btn btn-primary"
                            onClick={onClose}
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TodoHelp; 