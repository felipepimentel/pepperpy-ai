/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#5965DD',
                    dark: '#4752C4',
                    light: '#7B84E8',
                },
                secondary: '#6C757D',
                success: '#2ED47A',
                info: '#58A9DE',
                warning: '#F8B425',
                danger: '#F25767',
                light: '#F8F9FD',
                dark: '#1E2142',
            },
            spacing: {
                '4.5': '1.125rem', // 18px (4.5 * 4px)
            },
            boxShadow: {
                sm: '0 2px 8px rgba(0, 0, 0, 0.05)',
                md: '0 4px 12px rgba(0, 0, 0, 0.08)',
                lg: '0 8px 24px rgba(0, 0, 0, 0.12)',
            },
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
    ],
} 