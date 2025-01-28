import React, { useState, useEffect } from "react";
import "./Check.css";
import Axios from "axios";
import Delete from "../Delete/Delete";
import StatusApdater from "../StatusApdater/StatusApdater";

export default function Check({ task }) {
    const [showButtons, setShowButtons] = useState(false);
    const [message, setMessage] = useState("");
    const [currentDate, setCurrentDate] = useState("");
    const [expired, setExpired] = useState(false);
    const [status, setStatus] = useState(task.Status);
    const [containerClass, setContainerClass] = useState(() => {
        switch (status) {
        case "True":
            return 'info-container done';
        case "False":
            return 'info-container not-done';
        case "in progress":
            return 'info-container in-progress';
        case "not started":
            return 'info-container not-started';
        case "expiring":
            return 'info-container expiring';
        case "expired":
            return 'info-container expired';
        default:
            return 'info-container';
        }
      });


    useEffect(() => {
        const today = new Date();
        const month = today.getMonth() + 1;
        const year = today.getFullYear();
        const date = today.getDate();
        setCurrentDate(`${month}/${date}/${year}`);
    }, []);

    const ONE_DAY_IN_MILLIS = 24 * 60 * 60 * 1000; // Constant for one day in milliseconds

    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            const deadline = new Date(task.Deadline);
    
            if (status === "True" || status === "expiring" || status === "in progress" || status === "not started") {
                if (now > deadline) {
                    setExpired(true);
                    setMessage('Task expired');
                    setStatus("expired");
                    setContainerClass('info-container expired');
                    handleChange("expired");
                } else if (deadline - now <= ONE_DAY_IN_MILLIS && status !== "expiring") {
                    setStatus("expiring");
                    setContainerClass('info-container expiring');
                    handleChange("expiring");
                }
            }
        }, 1000);
    
        return () => {
            clearInterval(interval);
        };
    }, [task.Deadline, status]); // Ensure all dependencies are added


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

    const handleChange = (newStatus) => {
        const csrfToken = getCsrfToken();

        Axios.post('http://127.0.0.1:8000/update_task', {
            'index': task.id,
            'status': newStatus // Send the updated status
        }, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            withCredentials: true
        })
        .then(res => {
            console.log(res);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    };

    function handleHover() {
        setShowButtons(status && (status === "True" || status === "expiring"||status === "in progress"||status === "not started"));
    }

    function handleYes() {
        setStatus("done"); // Update local status
        handleChange("done"); // Update status on the server
        setShowButtons(false);
        setMessage('Task Done');
        setContainerClass('info-container done');
    }

    function handleNo() {
        setStatus(false); // Update local status
        handleChange(false); // Update status on the server
        setShowButtons(false);
        setMessage('Task not done');
        setContainerClass('info-container not-done');
    }

    return (
        <div className={containerClass} onMouseEnter={handleHover} onMouseLeave={() => setShowButtons(false)}>
            {showButtons ? (
                <div className="overlay">
                    <div className="message">Check it?</div>
                    <div className="confirmation-buttons">
                        <button className="translucent-button yes-button" onClick={handleYes}>Yes</button>
                        <button className="translucent-button no-button" onClick={handleNo}>No</button>
                    </div>
                </div>
            ) : null}
            <Delete task={task}/>
            <h3>{task.Title}</h3>
            <p>{task.About}</p>
            <p>{status}</p>
            <p>{new Date(task.DateAdded).toISOString().split('T')[0]}</p>
            <p>{new Date(task.Deadline).toISOString().split('T')[0]}</p>
            {message && <div className="message">{message} on {currentDate}</div>}
            {expired && <div className="message">Task expired</div>}
        </div>
    );
}
