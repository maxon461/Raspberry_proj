const API_BASE_URL = process.env.NODE_ENV === 'production' 
    ? window.location.origin 
    : `http://${window.location.hostname}:8000`;

export const getApiUrl = (endpoint) => `${API_BASE_URL}${endpoint}`;

export const fetchConfig = {
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.cookie.split('csrftoken=')[1]?.split(';')[0] || '',
    },
};

export const WS_BASE_URL = process.env.NODE_ENV === 'production'
    ? `ws://${window.location.host}`
    : `ws://${window.location.hostname}:8000`;

export const getWsUrl = (endpoint) => `${WS_BASE_URL}${endpoint}`;
