import React, { useEffect, useState } from 'react';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface NotificationProps {
    message: string;
    type?: NotificationType;
    duration?: number;
    onClose?: () => void;
    show: boolean;
}

const Notification: React.FC<NotificationProps> = ({
    message,
    type = 'info',
    duration = 5000,
    onClose,
    show
}) => {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (show) {
            setVisible(true);
            if (duration > 0) {
                const timer = setTimeout(() => {
                    setVisible(false);
                    if (onClose) onClose();
                }, duration);
                return () => clearTimeout(timer);
            }
        } else {
            setVisible(false);
        }
    }, [show, duration, onClose]);

    if (!visible) return null;

    // Type-specific configuration
    const config = {
        success: {
            bgColor: 'bg-success text-white',
            icon: 'bi-check-circle-fill'
        },
        error: {
            bgColor: 'bg-danger text-white',
            icon: 'bi-exclamation-triangle-fill'
        },
        warning: {
            bgColor: 'bg-warning text-dark',
            icon: 'bi-exclamation-circle-fill'
        },
        info: {
            bgColor: 'bg-info text-white',
            icon: 'bi-info-circle-fill'
        }
    };

    const { bgColor, icon } = config[type];

    return (
        <div
            className={`
        fixed bottom-4 right-4 max-w-sm p-4 rounded-lg shadow-lg transform transition-all 
        ${bgColor} animate-[fadeIn_0.3s_ease-in-out]
      `}
            role="alert"
        >
            <div className="flex items-center">
                <i className={`bi ${icon} mr-2`}></i>
                <span className="font-medium">{message}</span>
                <button
                    className="ml-auto -mx-1.5 -my-1.5 bg-white/20 text-white hover:bg-white/30 rounded-lg p-1.5"
                    onClick={() => {
                        setVisible(false);
                        if (onClose) onClose();
                    }}
                >
                    <span className="sr-only">Close</span>
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path>
                    </svg>
                </button>
            </div>
        </div>
    );
};

export default Notification; 