import React from 'react';
import './LoadingScreen.css';

const LoadingScreen = ({ isMusicPlaying, toggleMusic, volume, handleVolumeChange, showVolumeSlider, setShowVolumeSlider }) => {
    return (
        <div className="loading-screen">
            <div className="sound-controls">
                <button 
                    className="sound-button"
                    onClick={toggleMusic}
                    title={isMusicPlaying ? "Pause Music" : "Play Music"}
                >
                    {isMusicPlaying ? "🔊" : "🔈"}
                </button>
                <div className="volume-control">
                    <button 
                        className="sound-button"
                        onClick={() => setShowVolumeSlider(!showVolumeSlider)}
                        title="Volume Control"
                    >
                        🎵
                    </button>
                    {showVolumeSlider && (
                        <input 
                            type="range" 
                            min="0" 
                            max="1" 
                            step="0.1" 
                            value={volume}
                            onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                            className="volume-slider"
                        />
                    )}
                </div>
            </div>
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
                    Starter Pokédex
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
