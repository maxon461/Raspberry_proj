import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import "./Create.css"
import Axios from "axios";
import CurrentTime from '../CurrentTime/CurrentTime';

export default function Create() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        expiration_date: '',
        priority: 0
    });
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState('');

    // Setup WebSocket connection
    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8000/ws/gym_cards/');
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'rfid_timeout') {
                setIsLoading(false);
                setMessage('RFID card timeout');
                navigate('/'); // Immediate navigation
            } else if (data.type === 'card_update' && data.card.rfid_card_id) {
                setIsLoading(false);
                setMessage('Card created successfully!');
                navigate('/'); // Immediate navigation
            }
        };

        return () => ws.close();
    }, [navigate]);

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

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setMessage('');
        
        try {
            const response = await Axios.post('http://127.0.0.1:8000/api/create_gym_card_with_page/', formData, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                withCredentials: true
            });

            if (response.data.status === 'waiting_for_card') {
                setMessage('Please scan your RFID card...');
                // Timeout will be handled by WebSocket message
            } else if (response.data.status === 'error') {
                setIsLoading(false);
                setMessage(response.data.message);
            }
        } catch (error) {
            console.error('Error:', error);
            setIsLoading(false);
            setMessage('Error creating card');
        }
    };

    return (
        <>
            <CurrentTime />
            <div className="create">
                <h1>Create New Gym Card</h1>
                {message && <div className="message">{message}</div>}
                {isLoading ? (
                    <div className="loading-overlay">
                        <div className="loading-spinner"></div>
                        <p>Please scan your RFID card...</p>
                    </div>
                ) : (
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
                )}
            </div>
        </>
    );
}
