import React from "react";
import './App.css';
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import MainPage from "./Components/MainPage/MainPage";
import Create from "./Components/Create/Create";
import ReactDOM from 'react-dom/client'; // Correct import

export default function App() {
  return (
    <BrowserRouter>
      <h1>My Gym</h1>
      <nav>
        <ul>
          <li>
            <Link to="/">Home</Link> {/* Use Link for navigation */}
          </li>
          <li>
            <Link to="/create">Create</Link>
          </li>
        </ul>
      </nav>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/create" element={<Create />} />
      </Routes>
    </BrowserRouter>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

