import React, { useState } from 'react';
import "./Delete.css"
import Axios from "axios";

export default function Delete({task, showDots = true, className = 'delete'}) {
    const [showText, setShowText] = useState(false);
    
    const handleHover = () => {
        setShowText(true);
    };
    
    const getCsrfToken = () => {
        let csrfToken = null;
        const cookies = document.cookie.split(';');
        cookies.forEach(cookie => {
            if (cookie.trim().startsWith('csrftoken=')) {
                csrfToken = cookie.trim().substring('csrftoken='.length);
            }
        });
        return csrfToken;
    };

    const Deliting = () => {
        const csrfToken = getCsrfToken();
        Axios.post('http://127.0.0.1:8000/delete_task', {
            'task': task
        }, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            withCredentials: true
        })
        .then(res => {
            console.log(res);
            window.location.href = '/';
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    return (
        <div className={className} onMouseEnter={handleHover} onMouseLeave={() => setShowText(false)}>
            {showDots ? (
                <p>{showText ? <span onClick={Deliting}>Delete</span> : <span>...</span>}</p>
            ) : (
                <p onClick={Deliting}>Delete</p>
            )}
        </div>
    );
}
