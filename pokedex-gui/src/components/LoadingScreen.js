import React from 'react';
import './LoadingScreen.css';

const LoadingScreen = () => {
    return (
        <div className="loading-screen">
            <div className="blue-light"></div>
            <div className="indicator-lights">
                <div className="light light-red"></div>
                <div className="light light-yellow"></div>
                <div className="light light-green"></div>
            </div>
            
            <div className="loading-container">
                <div className="logo-container">
                    <img src="/logo192.png" alt="Pokedex Logo" className="logo-image" />
                </div>
                
                <div className="loading-text">
                    Initializing Pokédex
                    <span className="dot-1">.</span>
                    <span className="dot-2">.</span>
                    <span className="dot-3">.</span>
                </div>
                
                <div className="loading-bar">
                    <div className="loading-progress"></div>
                </div>
            </div>
        </div>
    );
};

export default LoadingScreen;
