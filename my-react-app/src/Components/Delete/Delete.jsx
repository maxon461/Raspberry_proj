import React from 'react';
import Axios from 'axios';
import './Delete.css';

const Delete = ({ card, showDots = true, className = '' }) => {
  const handleDelete = () => {
    if (!card || !card.id) {
      console.error('No card ID provided for deletion');
      return;
    }

    Axios.post('http://127.0.0.1:8000/api/delete_gym_card/', {
      id: card.id
    })
    .then(response => {
      if (response.data.status === 'success') {
        window.location.reload();
      }
    })
    .catch(error => {
      console.error('Error deleting card:', error);
    });
  };

  return (
    <button 
      onClick={handleDelete}
      className={`delete-button ${className}`}
      title="Delete card"
    >
      {showDots ? '...' : '×'}
    </button>
  );
};

export default Delete;

