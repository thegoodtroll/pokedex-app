import React, { useState, useRef } from 'react';
import './PokemonSpeaker.css';

const PokemonSpeaker = ({ pokemonName, isActive, onStartSpeak, onEndSpeak }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [audioElement, setAudioElement] = useState(null);
    const audioCache = useRef(new Map());
    const API_URL = "https://flask-backend-150344248755.europe-west1.run.app";

    const handleSpeak = async () => {
        if (isPlaying) {
            if (audioElement) {
                audioElement.pause();
                audioElement.currentTime = 0;
                onEndSpeak();
            }
            setIsPlaying(false);
            return;
        }

        // Check if audio is cached
        if (audioCache.current.has(pokemonName)) {
            const cachedAudio = new Audio(audioCache.current.get(pokemonName));
            setAudioElement(cachedAudio);
            
            cachedAudio.onended = () => {
                setIsPlaying(false);
                onEndSpeak();
            };

            onStartSpeak();
            cachedAudio.play();
            setIsPlaying(true);
            return;
        }

        setIsLoading(true);
        try {
            // First get the Pokémon description
            const descResponse = await fetch(`${API_URL}/get-pokemon-description`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ pokemon_name: pokemonName }),
            });

            if (!descResponse.ok) {
                throw new Error('Failed to get Pokémon description');
            }

            const descData = await descResponse.json();
            
            // Then convert it to speech
            const audioResponse = await fetch(`${API_URL}/text-to-speech`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: descData.description }),
            });

            if (!audioResponse.ok) {
                throw new Error('Failed to generate speech');
            }

            const audioBlob = await audioResponse.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Cache the audio URL
            audioCache.current.set(pokemonName, audioUrl);
            
            const audio = new Audio(audioUrl);
            setAudioElement(audio);
            
            audio.onended = () => {
                setIsPlaying(false);
                setIsLoading(false);
                onEndSpeak();
            };

            onStartSpeak();
            audio.play();
            setIsPlaying(true);
            setIsLoading(false);

        } catch (error) {
            console.error('Error in text-to-speech:', error);
            setIsPlaying(false);
            setIsLoading(false);
            onEndSpeak();
        }
    };

    return (
        <div className={`pokemon-speaker ${isActive ? 'active' : ''}`}>
            <button 
                className={`speaker-button ${isPlaying ? 'playing' : ''} ${isLoading ? 'loading' : ''}`}
                onClick={handleSpeak}
                disabled={!isActive || isLoading}
                title={!isActive ? "No Pokémon detected" : isLoading ? "Loading..." : "Click to hear description"}
            >
                {isLoading ? (
                    <div className="loading-circle"></div>
                ) : isPlaying ? '🔊' : '🔈'}
            </button>
            {isPlaying && !isLoading && (
                <div className="sound-wave">
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                    <div className="bar"></div>
                </div>
            )}
        </div>
    );
};

export default PokemonSpeaker;
