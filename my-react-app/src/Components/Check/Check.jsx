import React, { useState, useEffect } from "react";
import "./Check.css";
import Axios from "axios";
import Delete from "../Delete/Delete";

export default function Check({ card }) {
    const [showButtons, setShowButtons] = useState(false);
    const [message, setMessage] = useState("");
    const [currentDate, setCurrentDate] = useState("");
    const [expired, setExpired] = useState(false);
    const [status, setStatus] = useState(card.Status);
    const [containerClass, setContainerClass] = useState(() => {
        switch(card.Status) {
            case 'active':
                return 'info-container active';
            case 'inactive':
                return 'info-container inactive';
            case 'expired':
                return 'info-container expired';
            case 'deactivated':
                return 'info-container deactivated';
            case 'suspended':
                return 'info-container suspended';
            default:
                return 'info-container';
        }
    });

    const getContainerClass = (status) => {
        switch(status) {
            case 'active':
                return 'info-container active';
            case 'inactive':
                return 'info-container inactive';
            case 'expired':
                return 'info-container expired';
            case 'deactivated':
                return 'info-container deactivated';
            case 'suspended':
                return 'info-container suspended';
            default:
                return 'info-container';
        }
    };

    useEffect(() => {
        const today = new Date();
        const month = today.getMonth() + 1;
        const year = today.getFullYear();
        const date = today.getDate();
        setCurrentDate(`${month}/${date}/${year}`);
    }, []);

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            const expiration = new Date(card.ExpirationDate);
    
            if (now > expiration && status && !expired && !card.IsExpired) {
                setExpired(true);
                setMessage('Card expired');
                setStatus(false);
                setContainerClass('info-container inactive');
                
                // Send expiration update to server
                const csrfToken = getCsrfToken();
                Axios.post('http://127.0.0.1:8000/api/mark_card_expired/', {
                    'id': card.id
                }, {
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    withCredentials: true
                })
                .catch(error => {
                    console.error('Error marking card as expired:', error);
                });
            }
        }, 60000);  // Check every minute
    
        // Initial check
        if (card.IsExpired) {
            setExpired(true);
            setStatus(false);
            setContainerClass('info-container inactive');
        }
    
        return () => clearInterval(interval);
    }, [card.ExpirationDate, status, expired, card.IsExpired]);

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

    const handleStatusChange = (newStatus) => {
        const csrfToken = getCsrfToken();

        Axios.post('http://127.0.0.1:8000/api/update_gym_card/', {
            'id': card.id,
            'status': newStatus,
            'priority': card.Priority,
            'is_expired': false  // Reset expired status when activating
        }, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            withCredentials: true
        })
        .then(res => {
            setStatus(newStatus);
            setContainerClass(getContainerClass(newStatus));
            if (newStatus === 'active') {
                window.location.reload(); // Reload on activation
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    };

    function handleHover() {
        // Only disable hover for expired cards, not deactivated ones
        setShowButtons(!expired);
    }

    function handleActivate() {
        setStatus('active');  // Change from true to 'active'
        handleStatusChange('active');
        setShowButtons(false);
        setMessage('Card Activated');
        setContainerClass('info-container active');
        window.location.reload(); // Add reload to ensure UI consistency
    }

    function handleDeactivate() {
        setStatus('deactivated');
        handleStatusChange('deactivated');
        setShowButtons(false);
        setMessage('Card Deactivated');
        setContainerClass('info-container deactivated');
        window.location.reload(); // Add reload to refresh the view
    }

    const handleDelete = async (id) => {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/delete_gym_card/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: id })
            });

            if (response.ok) {
                console.log('Card deleted successfully');
                // Optionally refresh the page or update UI
                window.location.reload();
            } else {
                console.error('Failed to delete card');
            }
        } catch (error) {
            console.error('Error deleting card:', error);
        }
    };

    return (
        <div className={containerClass} onMouseEnter={handleHover} onMouseLeave={() => setShowButtons(false)}>
            {showButtons ? (
                <div className="overlay">
                    <div className="message">Change status?</div>
                    <div className="confirmation-buttons">
                        <button 
                            className="translucent-button yes-button" 
                            onClick={handleActivate}
                            disabled={expired} // Only disable if expired, not if deactivated
                        >
                            Activate
                        </button>
                        <button 
                            className="translucent-button no-button" 
                            onClick={handleDeactivate}
                        >
                            Deactivate
                        </button>
                    </div>
                </div>
            ) : null}
            <Delete 
                onDelete={(id) => handleDelete(id)} 
                cardId={card.id}
            />
            <h3>{card.Title}</h3>
            <p>{card.Description}</p>
            <p>Status: {card.Status.charAt(0).toUpperCase() + card.Status.slice(1)}</p>
            <p>Added: {new Date(card.DateAdded).toLocaleDateString()}</p>
            <p>Expires: {new Date(card.ExpirationDate).toLocaleDateString()}</p>
            <p>Priority: {card.Priority}</p>
            {card.rfid_card_id && <p>RFID: {card.rfid_card_id}</p>}
            {message && <div className="message">{message} on {currentDate}</div>}
            {expired && <div className="message">Card expired</div>}
        </div>
    );
}

