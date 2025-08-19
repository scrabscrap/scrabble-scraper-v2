// This file is part of the scrabble-scraper-v2 distribution
// Copyright (c) 2025 Rainer Rohloff.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
// General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.

import React from 'react';

import { DataProvider } from "./context/DataContext";
import { Display } from './components/Display';

interface ErrorBoundaryProps {
    children: React.ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    state = { hasError: false };

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return <h1>Something went wrong.</h1>;
        }
        return this.props.children;
    }
}
function App() {
    return (
        <ErrorBoundary>
            <DataProvider>
                <Display />
            </DataProvider>
        </ErrorBoundary>
    );
    // <div className='row py-1'>
    //     <pre>{JSON.stringify(data, null, 2)}</pre>
    // </div>
}
export default App;
