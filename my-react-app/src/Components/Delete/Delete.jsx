import React from 'react';
import './Delete.css';

const Delete = ({ onDelete, cardId, showDots = true, className = '' }) => {
  const handleClick = (e) => {
    e.preventDefault();
    if (typeof onDelete === 'function') {
      onDelete(cardId);
    } else {
      console.error('onDelete is not a function');
    }
  };

  return (
    <button 
      onClick={handleClick}
      className={`delete-button ${className}`}
      title="Delete card"
    >
      {showDots ? '...' : '🗑️'}
    </button>
  );
};

export default Delete;

