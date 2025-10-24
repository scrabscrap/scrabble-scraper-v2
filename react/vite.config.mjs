import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import loadVersion from 'vite-plugin-package-version';
import * as child from "child_process";

const commitHash = child.execSync("git rev-parse --short HEAD").toString().replace('\n', '');
const commitTag = child.execSync("git describe --tags").toString().replace('\n', '');

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