import React, { useState, useEffect, useRef } from 'react';
import Axios from 'axios';
import CurrentTime from '../CurrentTime/CurrentTime';
import Check from '../Check/Check';
import Toggle from '../Toggle/Toggle';
import ShowTable from '../ShowTable/ShowTable';
import './MainPage.css';

const MainPage = () => {
  const [gymCards, setGymCards] = useState([]);
  const wsRef = useRef(null);
  const [isToggled, setIsToggled] = useState(() => {
    const savedState = localStorage.getItem('toggleState');
    return savedState === 'true';
  });
  const [isLoading, setIsLoading] = useState(true);

  const fetchGymCards = async () => {
    try {
      const response = await Axios.get('http://127.0.0.1:8000/api/get_gym_cards/');
      if (response.data && Array.isArray(response.data.gym_cards)) {
        setGymCards(response.data.gym_cards);
      }
    } catch (error) {
      console.error('Error fetching gym cards:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGymCards();

    wsRef.current = new WebSocket('ws://127.0.0.1:8000/ws/gym_cards/');
    
    wsRef.current.onopen = () => {
      console.log('WebSocket Connected');
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);

        if (data.type === 'delete') {
          // Remove card using the ID from data.data
          setGymCards(prevCards => 
            prevCards.filter(card => card.id !== data.data.id)
          );
        } else if (data.type === 'card_update') {
          setGymCards(prevCards => {
            const newCards = [...prevCards];
            const index = newCards.findIndex(card => card.id === data.data.id);
            
            if (index !== -1) {
              newCards[index] = { ...newCards[index], ...data.data };
            } else {
              newCards.push(data.data);
            }
            
            return newCards;
          });
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    // Reconnection logic
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected. Reconnecting...');
      setTimeout(() => {
        if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
          window.location.reload();
        }
      }, 1000);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleToggleChange = (state) => {
    setIsToggled(state);
    localStorage.setItem('toggleState', state);
  };

  const handleDelete = async (cardId) => {
    try {
        const response = await fetch('/api/delete_gym_card/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id: cardId })
        });
        
        if (response.ok) {
            // Local state update will happen through WebSocket
            console.log('Card deleted successfully');
        } else {
            console.error('Failed to delete card');
        }
    } catch (error) {
        console.error('Error:', error);
    }
};

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="main-container">
      <CurrentTime />
      <Toggle onToggle={handleToggleChange} />

      <div className="content-container">
        {isToggled ? (
          <div className="table-container">
            {gymCards.length > 0 ? (
              <ShowTable data={gymCards} />
            ) : (
              <p>No gym cards available</p>
            )}
          </div>
        ) : (
          <div className="grid-container">
            {gymCards.length > 0 ? (
              gymCards.map(card => (
                <Check 
                  key={`card-${card.id}`}
                  card={card}
                />
              ))
            ) : (
              <p>No gym cards available</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MainPage;
