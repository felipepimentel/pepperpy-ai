import { useEffect, useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ExecutionResult } from '../store/workflowStore';

interface ResultViewerProps {
  result: ExecutionResult | null;
  onCopy?: () => void;
}

const ResultViewer: React.FC<ResultViewerProps> = ({ result, onCopy }) => {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (copied) {
      const timer = setTimeout(() => setCopied(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [copied]);

  if (!result) {
    return null;
  }

  const formattedJson = JSON.stringify(result, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(formattedJson);
    setCopied(true);
    if (onCopy) onCopy();
  };

  return (
    <div className="card mt-5">
      <div className="card-header">
        <div className="flex items-center gap-2">
          <span 
            className={`badge ${result.status === 'success' ? 'badge-success' : 'badge-danger'}`}
          >
            {result.status === 'success' ? 'Success' : 'Error'}
          </span>
          {result.execution_time && (
            <span className="text-xs text-secondary">
              {result.execution_time.toFixed(2)}s
            </span>
          )}
        </div>

        <button 
          className="btn btn-secondary p-1.5 h-8 w-8"
          onClick={handleCopy}
          title="Copy to clipboard"
        >
          {copied ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
              <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
            </svg>
          )}
        </button>
      </div>
      <div className="rounded-b-lg overflow-auto max-h-[400px] bg-[#1E1E1E]">
        <SyntaxHighlighter
          language="json"
          style={vscDarkPlus}
          customStyle={{ margin: 0, padding: '1rem', borderRadius: '0 0 0.5rem 0.5rem' }}
        >
          {formattedJson}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

export default ResultViewer; 