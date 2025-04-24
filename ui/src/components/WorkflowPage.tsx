import { useEffect, useState } from 'react';
import useNotificationStore from '../store/notificationStore';
import useWorkflowStore from '../store/workflowStore';
import CodeEditor from './CodeEditor';
import Notification from './Notification';
import ResultViewer from './ResultViewer';
import Todo from './Todo';
import WorkflowList from './WorkflowList';

const WorkflowPage = () => {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [showTodos, setShowTodos] = useState(false);

    // Get workflow state and actions
    const {
        workflows,
        isLoading,
        error,
        currentWorkflow,
        currentSchema,
        inputData,
        configData,
        executionResult,
        fetchWorkflows,
        setCurrentWorkflow,
        updateInputData,
        updateConfigData,
        executeWorkflow,
        resetExecutionResult
    } = useWorkflowStore();

    // Get notification state and actions
    const {
        message,
        type,
        show,
        showNotification,
        hideNotification
    } = useNotificationStore();

    // Load workflows on component mount
    useEffect(() => {
        fetchWorkflows();
    }, [fetchWorkflows]);

    // Handle workflow selection
    const handleWorkflowSelect = (id: string) => {
        setCurrentWorkflow(id);
        resetExecutionResult();
    };

    // Handle workflow execution
    const handleExecuteWorkflow = async () => {
        try {
            // Validate input/config JSON
            JSON.parse(inputData);
            JSON.parse(configData);

            await executeWorkflow();
        } catch (error: any) {
            showNotification(
                error.message || 'Invalid JSON. Please check your input data and configuration.',
                'error'
            );
        }
    };

    // Toggle between workflow execution and todos
    const toggleTodos = () => {
        setShowTodos(!showTodos);
    };

    return (
        <div className="flex flex-col min-h-screen">
            {/* Navbar */}
            <header className="bg-gradient-to-r from-primary to-primary-dark text-white shadow-md">
                <div className="container mx-auto px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center">
                        <button
                            className="mr-3 md:hidden"
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                        >
                            <i className={`bi ${sidebarOpen ? 'bi-x' : 'bi-list'} text-xl`}></i>
                        </button>
                        <div className="flex items-center gap-2">
                            <img
                                src="/pepperpy-logo.svg"
                                alt="PepperPy"
                                className="h-8 w-8"
                                onError={(e) => {
                                    e.currentTarget.onerror = null;
                                    e.currentTarget.src = 'https://via.placeholder.com/32/5965DD/FFFFFF?text=P';
                                }}
                            />
                            <h1 className="text-xl font-semibold">PepperPy Playground</h1>
                        </div>
                    </div>

                    <nav className="flex gap-4">
                        <a href="https://github.com/example/pepperpy" className="text-white/80 hover:text-white" target="_blank" rel="noreferrer">
                            <i className="bi bi-github text-xl"></i>
                        </a>
                        <a href="/docs" className="text-white/80 hover:text-white">
                            <i className="bi bi-book text-xl"></i>
                        </a>
                    </nav>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* Sidebar */}
                <aside
                    className={`
            w-64 bg-white border-r border-gray-200 overflow-y-auto
            transition-all duration-300 ease-in-out
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            md:translate-x-0 md:relative absolute z-10 h-[calc(100vh-60px)]
          `}
                >
                    <WorkflowList
                        workflows={workflows}
                        currentWorkflow={currentWorkflow}
                        isLoading={isLoading}
                        error={error}
                        onSelect={handleWorkflowSelect}
                        onRefresh={fetchWorkflows}
                    />
                </aside>

                {/* Main content */}
                <main className="flex-1 overflow-y-auto p-4 bg-gray-50">
                    <div className="max-w-5xl mx-auto">
                        {currentWorkflow && currentSchema ? (
                            <>
                                <div className="mb-6">
                                    <h2 className="text-2xl font-bold mb-2">{currentSchema.name}</h2>
                                    <p className="text-secondary">{currentSchema.description}</p>

                                    {currentSchema.version && (
                                        <div className="mt-2">
                                            <span className="badge badge-primary">v{currentSchema.version}</span>
                                        </div>
                                    )}
                                </div>

                                {/* Toggle between workflow and todos */}
                                <div className="flex justify-end mb-4">
                                    <div className="btn-group">
                                        <button
                                            className={`btn ${!showTodos ? 'btn-primary' : 'btn-secondary'}`}
                                            onClick={() => setShowTodos(false)}
                                        >
                                            <i className="bi bi-play-fill me-1"></i> Workflow
                                        </button>
                                        <button
                                            className={`btn ${showTodos ? 'btn-primary' : 'btn-secondary'}`}
                                            onClick={() => setShowTodos(true)}
                                        >
                                            <i className="bi bi-list-check me-1"></i> Tasks
                                        </button>
                                    </div>
                                </div>

                                {!showTodos ? (
                                    // Workflow Section
                                    <>
                                        <div className="grid md:grid-cols-2 gap-4 mb-4">
                                            <div className="card">
                                                <div className="card-header font-medium">
                                                    Input Data
                                                </div>
                                                <div className="card-body p-0">
                                                    <CodeEditor
                                                        value={inputData}
                                                        onChange={updateInputData}
                                                        language="json"
                                                        height="300px"
                                                    />
                                                </div>
                                            </div>

                                            <div className="card">
                                                <div className="card-header font-medium">
                                                    Configuration
                                                </div>
                                                <div className="card-body p-0">
                                                    <CodeEditor
                                                        value={configData}
                                                        onChange={updateConfigData}
                                                        language="json"
                                                        height="300px"
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex justify-center mb-6">
                                            <button
                                                className="btn btn-primary"
                                                onClick={handleExecuteWorkflow}
                                                disabled={isLoading}
                                            >
                                                {isLoading ? (
                                                    <>
                                                        <span className="animate-spin h-5 w-5 border-t-2 border-b-2 border-white rounded-full"></span>
                                                        <span>Executing...</span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <i className="bi bi-play-fill"></i>
                                                        <span>Execute Workflow</span>
                                                    </>
                                                )}
                                            </button>
                                        </div>

                                        {executionResult && (
                                            <ResultViewer
                                                result={executionResult}
                                                onCopy={() => showNotification('Result copied to clipboard', 'success')}
                                            />
                                        )}
                                    </>
                                ) : (
                                    // Todo Section
                                    <Todo workflowId={currentWorkflow} />
                                )}
                            </>
                        ) : (
                            <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
                                <div className="text-6xl text-primary/20 mb-4">
                                    <i className="bi bi-diagram-3"></i>
                                </div>
                                <h2 className="text-2xl font-semibold mb-2">Select a Workflow</h2>
                                <p className="text-secondary mb-6 max-w-md">
                                    Choose a workflow from the sidebar to get started
                                </p>

                                {sidebarOpen === false && (
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => setSidebarOpen(true)}
                                    >
                                        <i className="bi bi-list me-2"></i>
                                        <span>Show Workflows</span>
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                </main>
            </div>

            {/* Footer */}
            <footer className="bg-white border-t border-gray-200 py-4 text-center">
                <div className="text-sm text-secondary">
                    <span>PepperPy Playground &copy; {new Date().getFullYear()}</span>
                </div>
            </footer>

            {/* Notification */}
            <Notification
                message={message}
                type={type}
                show={show}
                onClose={hideNotification}
            />
        </div>
    );
};

export default WorkflowPage; 