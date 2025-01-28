import React, { useState, useEffect } from 'react';
import './Toggle.css';

const Toggle = ({ onToggle }) => {
  const [isToggled, setIsToggled] = useState(() => {
    const savedState = localStorage.getItem('toggleState');
    return savedState === 'true';
  });

  useEffect(() => {
    localStorage.setItem('toggleState', isToggled);
    onToggle(isToggled);
  }, [isToggled, onToggle]);

  const handleToggle = () => {
    setIsToggled(prevState => !prevState);
  };

  return (
    <div className="toggle-container">
      <div className={`toggle-button ${isToggled ? 'on' : 'off'}`} onClick={handleToggle}>
        <div className="toggle-circle"></div>
      </div>
    </div>
  );
};

export default Toggle;
