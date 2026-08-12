import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/** Ne pas proxifier les URLs exactes des routes React (SPA) vers FastAPI. */
function bypassSpaRoot(req, segment) {
    const path = (req.url?.split("?")[0] ?? "").replace(/\/$/, "") || "/";
    const root = `/${segment}`;
    if (path === root) return false;
    return undefined;
}

export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            "/followup": {
                target: "http://localhost:8000",
                changeOrigin: true,
                bypass(req) {
                    return bypassSpaRoot(req, "followup");
                },
            },
            "/persona": {
                target: "http://localhost:8000",
                changeOrigin: true,
                bypass(req) {
                    return bypassSpaRoot(req, "persona");
                },
            },
            "/heatmap": {
                target: "http://localhost:8000",
                changeOrigin: true,
                bypass(req) {
                    return bypassSpaRoot(req, "heatmap");
                },
            },
        },
    },
});