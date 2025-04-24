import { useEffect, useRef } from 'react';

// CodeEditor props
interface CodeEditorProps {
    value: string;
    onChange: (value: string) => void;
    language?: string;
    height?: string;
    placeholder?: string;
}

// We're using the Ace Editor loaded from CDN
declare global {
    interface Window {
        ace: any;
    }
}

const CodeEditor = ({
    value,
    onChange,
    language = 'json',
    height = '300px',
    placeholder = '',
}: CodeEditorProps) => {
    const editorRef = useRef<HTMLDivElement>(null);
    const aceEditorRef = useRef<any>(null);

    useEffect(() => {
        // Load Ace Editor from CDN if not already loaded
        if (!window.ace) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/ace/1.23.4/ace.js';
            script.integrity = 'sha512-W2EhLYb/QT7Q8fLcvmTk0OacGjgHQZJJvKYKDQQdQGX7icS0l0hK5zxr+lHXpXFemR5Gsb4s0Jl4UmUBptwZYQ==';
            script.crossOrigin = 'anonymous';
            script.referrerPolicy = 'no-referrer';
            script.async = true;

            script.onload = initializeEditor;
            document.body.appendChild(script);
        } else {
            initializeEditor();
        }

        return () => {
            // Cleanup on unmount
            if (aceEditorRef.current) {
                aceEditorRef.current.destroy();
            }
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // Initialize the editor
    const initializeEditor = () => {
        if (!editorRef.current || !window.ace) return;

        // Create editor instance
        aceEditorRef.current = window.ace.edit(editorRef.current);
        aceEditorRef.current.setTheme('ace/theme/monokai');
        aceEditorRef.current.session.setMode(`ace/mode/${language}`);
        aceEditorRef.current.setOptions({
            fontSize: '14px',
            showPrintMargin: false,
            showGutter: true,
            highlightActiveLine: true,
            wrap: true,
            tabSize: 2
        });

        // Set initial value
        aceEditorRef.current.setValue(value, -1);

        // Add change listener
        aceEditorRef.current.on('change', () => {
            onChange(aceEditorRef.current.getValue());
        });
    };

    // Update editor value when prop changes
    useEffect(() => {
        if (aceEditorRef.current && aceEditorRef.current.getValue() !== value) {
            aceEditorRef.current.setValue(value, -1);
        }
    }, [value]);

    return (
        <div
            ref={editorRef}
            className="border border-gray-200 rounded-md"
            style={{ height, width: '100%' }}
            placeholder={placeholder}
        />
    );
};

export default CodeEditor; 