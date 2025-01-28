import React, { useState } from 'react';
import "./Create.css"
import Axios from "axios";
import CurrentTime from '../CurrentTime/CurrentTime';

export default function Create() {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        expiration_date: '',
        priority: 0
    });

    const handleChange = (e) => {
        const value = e.target.type === 'number' ? 
            parseInt(e.target.value) : e.target.value;
        setFormData({
            ...formData,
            [e.target.name]: value
        });
    };

    const getCsrfToken = () => {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            if (cookie.trim().startsWith('csrftoken=')) {
                return cookie.trim().substring('csrftoken='.length);
            }
        }
        return null;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const csrfToken = getCsrfToken();

        Axios.post('http://127.0.0.1:8000/create_gym_card/', formData, {  // Note the trailing slash
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
        .catch(error => console.error('Error:', error));
    };

    return (
        <><CurrentTime />
        <div className="create">
            <h1>Create New Gym Card</h1>
            <form onSubmit={handleSubmit}>
                <label htmlFor="title">Title: </label>
                <input 
                    type="text" 
                    id="title" 
                    name="title" 
                    required
                    onChange={handleChange}
                />

                <label htmlFor="description">Description:</label>
                <textarea 
                    id="description" 
                    name="description" 
                    required
                    onChange={handleChange}
                />

                <label htmlFor="expiration_date">Expiration Date:</label>
                <input 
                    type="datetime-local" 
                    id="expiration_date" 
                    name="expiration_date" 
                    required
                    onChange={handleChange}
                />

                <label htmlFor="priority">Priority:</label>
                <input 
                    type="number" 
                    id="priority" 
                    name="priority" 
                    min="0"
                    max="10"
                    value={formData.priority}
                    onChange={handleChange}
                />

                <button type="submit">Create Card</button>
            </form>
        </div></>
    );
}
