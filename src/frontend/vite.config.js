/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'node:path';
// ============================================
// SynapSeed — Vite + React + TS configuration
// ============================================
export default defineConfig({
    plugins: [react(), tailwindcss()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        host: '0.0.0.0',
        port: 5173,
        strictPort: true,
        // Proxy /api al backend en dev (evita problemas de CORS)
        proxy: {
            '/api': {
                target: process.env.VITE_API_URL ?? 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
    preview: {
        host: '0.0.0.0',
        port: 4173,
    },
    build: {
        target: 'es2022',
        sourcemap: true,
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ['react', 'react-dom', 'react-router-dom'],
                    query: ['@tanstack/react-query'],
                    forms: ['react-hook-form', 'zod', '@hookform/resolvers'],
                },
            },
        },
    },
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: ['./src/test/setup.ts'],
        css: true,
        coverage: {
            provider: 'v8',
            reporter: ['text', 'html', 'json'],
            exclude: [
                'node_modules/',
                'src/test/',
                '**/*.config.{ts,js}',
                '**/types/**',
            ],
        },
    },
});
