import React, { useState, useEffect } from 'react';
import Axios from 'axios';
import CurrentTime from '../CurrentTime/CurrentTime';
import Check from '../Check/Check';
import Toggle from '../Toggle/Toggle';
import ShowTable from '../ShowTable/ShowTable';
import './MainPage.css';

const MainPage = () => {
  const [gymCards, setGymCards] = useState([]);
  const [isToggled, setIsToggled] = useState(() => {
    const savedState = localStorage.getItem('toggleState');
    return savedState === 'true';
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const fetchGymCards = async () => {
      try {
        const response = await Axios.get('http://127.0.0.1:8000/get_gym_cards/');
        if (mounted && response.data && Array.isArray(response.data.gym_cards)) {
          const formattedCards = response.data.gym_cards.map(card => ({
            id: card.id,
            Title: card.Title,
            Description: card.Description,
            Status: card.Status || 'inactive',
            Priority: card.Priority || 0,
            ExpirationDate: card.ExpirationDate,
            DateAdded: card.DateAdded,
            IsExpired: card.IsExpired
          }));
          setGymCards(formattedCards);
        }
      } catch (error) {
        if (mounted) {
          console.error('Error fetching gym cards:', error);
          setGymCards([]);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    fetchGymCards();
    return () => {
      mounted = false;
    };
  }, []);

  const handleToggleChange = (state) => {
    setIsToggled(state);
    localStorage.setItem('toggleState', state);
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
