import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import loadVersion from 'vite-plugin-package-version';
import * as child from "child_process";

let commitHash = 'unknown';
let commitTag = 'unknown';

try {
    commitHash = child
        .execSync('git rev-parse --short HEAD', { stdio: ['ignore', 'pipe', 'ignore'] })
        .toString()
        .trim();
} catch (err) {
    console.warn('Could not determine git commit hash:', err && err.message ? err.message : err);
}

try {
    commitTag = child
        .execSync('git describe --tags', { stdio: ['ignore', 'pipe', 'ignore'] })
        .toString()
        .trim();
} catch (err) {
    commitTag = '(' + commitHash + ')';
    console.warn('Could not determine git tag:', err && err.message ? err.message : err);
}

export default defineConfig(() => {
    return {
        build: {
            outDir: 'build',
        },
        define: {
            'import.meta.env.VITE_APP_VERSION': JSON.stringify(commitHash),
            'import.meta.env.VITE_APP_TAG': JSON.stringify(commitTag),
        },
        base: '',
        server: {
            allowedHosts: ['.gitpod.io', 'localhost'],
        },
        plugins: [react(), loadVersion()],
    };
});