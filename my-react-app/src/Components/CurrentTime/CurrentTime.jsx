import React, { useState, useEffect } from 'react';
import "./CurrentTime.css"

export default function CurrentTime() {
    const [currentDate, setCurrentDate] = useState(getDate());

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentDate(getDate());
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    function getDate() {
        const today = new Date();
        const month = today.getMonth() + 1;
        const year = today.getFullYear();
        const date = today.getDate();
        return `${month}/${date}/${year}`;
    }

    return (
        <div className='current-time'>
            {currentDate}
        </div>
    );
}

