import "./Create.css"
import Axios from "axios";
import CurrentTime from '../CurrentTime/CurrentTime';
import React, { useState } from 'react';

export default function Create() {
    const [formData, setFormData] = useState({
        task: '',
        about: '',
        date: ''
    });

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        Axios.post(`http://127.0.0.1:8000/create`, {
            'task': formData.task,
            'about': formData.about,
            'date': formData.date,
        },
        {
            headers: {
                "Content-Type": 'application/json'
            }
        }
    )
        .then(res => {
            console.log(res);
            window.location.href = '/';
        })
        .catch(error => console.error(error));
    };

    return (
        <><CurrentTime /><div className="create">
            <h1>Create a new task</h1>
            <form onSubmit={handleSubmit}>
                <label htmlFor="task">Task: </label>
                <input type="text" id="task" name="task" onChange={handleChange}/>
                <label htmlFor="about">About:</label>
                <input type="text" id="about" name="about" onChange={handleChange}/>
                <label htmlFor="date">Date:</label>
                <input type="date" id="date" name="date" onChange={handleChange}/>
                <button type="submit">Create</button>
            </form>
        </div></>
    );
}