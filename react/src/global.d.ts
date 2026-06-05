declare module '*.css';
declare module '*.scss';
declare module '*.sass';
declare module '*.less';
declare module '*.svg';

declare interface ImportMeta {
    env: {
        VITE_APP_VERSION?: string;
        VITE_APP_TAG?: string;
        PACKAGE_VERSION?: string;
    };
}

