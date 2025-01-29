import React, { useState, useEffect } from "react";
import "./ShowTable.css";
import Delete from "../Delete/Delete";
import StatusApdater from "../StatusApdater/StatusApdater";

export default function ShowTable({ data }) {
  const [cards, setCards] = useState(data);

  // Update cards when data prop changes
  useEffect(() => {
    setCards(data);
  }, [data]);

  const [sortOrder, setSortOrder] = useState({
    Title: true,
    Description: true,
    Status: true,
    DateAdded: true,
    ExpirationDate: true,
    Priority: true
  });

  function sortBy(key) {
    const sortedCards = [...cards];
    const isAscending = sortOrder[key];

    sortedCards.sort((a, b) => {
      if (typeof a[key] === "string") {
        return isAscending
          ? a[key].localeCompare(b[key])
          : b[key].localeCompare(a[key]);
      } else if (key === 'Priority') {
        return isAscending ? a[key] - b[key] : b[key] - a[key];
      } else {
        return isAscending
          ? new Date(a[key]) - new Date(b[key])
          : new Date(b[key]) - new Date(a[key]);
      }
    });

    setCards(sortedCards);
    setSortOrder(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  }

  const handleDelete = async (cardId) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/delete_gym_card/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: cardId })
      });

      if (!response.ok) {
        throw new Error('Failed to delete card');
      }

      // Card removal will be handled by WebSocket message
      console.log('Delete request sent successfully');
    } catch (error) {
      console.error('Error deleting card:', error);
    }
  };

  if (!cards || cards.length === 0) {
    return <p>No cards available.</p>;
  }

  return (
    <table className="tasks-table">
      <thead>
        <tr>
          <th onClick={() => sortBy('Title')} className="sortable-header">Name</th>
          <th onClick={() => sortBy('Description')} className="sortable-header">Description</th>
          <th onClick={() => sortBy('Status')} className="sortable-header">Status</th>
          <th onClick={() => sortBy('DateAdded')} className="sortable-header">Date Added</th>
          <th onClick={() => sortBy('ExpirationDate')} className="sortable-header">Expiration Date</th>
          <th onClick={() => sortBy('Priority')} className="sortable-header">Priority</th>
          <th className="sortable-header">RFID</th>
          <th className="actions">Actions</th>
        </tr>
      </thead>
      <tbody>
        {cards.map((card) => (
          <tr key={card.id} className={card.IsExpired ? 'expired' : ''}>
            <td>{card.Title}</td>
            <td>{card.Description}</td>
            <td>{card.Status}</td>
            <td>{new Date(card.DateAdded).toLocaleDateString()}</td>
            <td>{new Date(card.ExpirationDate).toLocaleDateString()}</td>
            <td>{card.Priority}</td>
            <td>{card.rfid_card_id || 'Not assigned'}</td>
            <td className="actions-cell">
              <Delete 
                card={card} 
                onDelete={() => handleDelete(card.id)} 
                showDots={false} 
                className="delete-button" 
              />
              {!card.IsExpired && (
                <>
                  <StatusApdater
                    card={card}
                    newStatus="active"
                    className="activate-btn"
                  />
                  <StatusApdater
                    card={card}
                    newStatus="deactivated"
                    className="deactivate-btn"
                  />
                </>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
