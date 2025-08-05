// API Configuration for BookSouls Vector Indexer

// Determine API base URL based on environment
const getApiBaseUrl = () => {
    // In development, use the FastAPI server URL
    if (import.meta.env.DEV) {
        return 'http://localhost:8000';
    }

    // In production, you might want to use a different URL
    return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();
export const API_ENDPOINTS = {
    indexer: {
        initialize: `${API_BASE_URL}/api/indexer/initialize`,
        query: `${API_BASE_URL}/api/indexer/query`,
        stats: `${API_BASE_URL}/api/indexer/stats`,
        reset: `${API_BASE_URL}/api/indexer/reset`,
        index: `${API_BASE_URL}/api/indexer/index`,
        upload: `${API_BASE_URL}/api/indexer/index/upload`,
    },
    characters: {
        list: `${API_BASE_URL}/api/characters/list`,
        chat: `${API_BASE_URL}/api/characters/chat`,
    },
    health: `${API_BASE_URL}/api/health`,
};

// Helper function to make API calls with error handling
export const apiCall = async (url, options = {}) => {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, mergedOptions);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: response.statusText }));
            throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}; 