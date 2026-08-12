/** @type {import('tailwindcss').Config} */
export default {
    darkMode: "class",
    content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
    theme: {
        extend: {
            colors: {
                alia: {
                    primary: {
                        50: "#f0f9ff",
                        100: "#e0f2fe",
                        200: "#bae6fd",
                        300: "#7dd3fc",
                        400: "#38bdf8",
                        500: "#0ea5e9",
                        600: "#0284c7",
                        700: "#0369a1",
                        800: "#075985",
                        900: "#0c4a6e",
                    },
                    secondary: {
                        50: "#eef2ff",
                        100: "#e0e7ff",
                        200: "#c7d2fe",
                        300: "#a5b4fc",
                        400: "#818cf8",
                        500: "#6366f1",
                        600: "#4f46e5",
                        700: "#4338ca",
                        800: "#3730a3",
                        900: "#312e81",
                    },
                },
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
            },
            boxShadow: {
                soft: "0 10px 30px rgba(2, 6, 23, 0.08)",
            },
        },
    },
    plugins: [],
};