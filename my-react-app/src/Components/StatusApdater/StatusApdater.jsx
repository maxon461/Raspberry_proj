import React from 'react';
import Axios from 'axios';
import './StatusApdater.css';

const StatusApdater = ({ card, newStatus, className = '' }) => {
  const handleStatusChange = () => {
    if (!card || !card.id) {
      console.error('No card ID provided for status update');
      return;
    }

    Axios.post('http://127.0.0.1:8000/update_gym_card/', {
      id: card.id,
      status: newStatus,
      priority: card.Priority
    })
    .then(response => {
      if (response.data.status === 'success') {
        window.location.reload();
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
  };

  return (
    <button
      onClick={handleStatusChange}
      className={`status-button ${className}`}
      title={`Mark as ${newStatus}`}
    >
      {newStatus === 'active' ? '✓' : '⨯'}
    </button>
  );
};

export default StatusApdater;
