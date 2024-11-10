import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import cameraSound from './assets/camera.mp3';
import scanSound from './assets/scan.mp3';
import backgroundMusic from './assets/cerulean-city.wav';

// Define your Flask backend URL here
const API_URL = "https://pokedex-app-b83a.onrender.com";

function App() {
    const [capturedPhoto, setCapturedPhoto] = useState(null);
    const [capturedPhotoURL, setCapturedPhotoURL] = useState(null);
    const [predictedPokemon, setPredictedPokemon] = useState(null);
    const [pokemonImage, setPokemonImage] = useState(null);
    const [videoStream, setVideoStream] = useState(null);  
    const [isCameraActive, setIsCameraActive] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isMusicPlaying, setIsMusicPlaying] = useState(false);
    const [volume, setVolume] = useState(0.3);
    const [showVolumeSlider, setShowVolumeSlider] = useState(false);
    const [useFrontCamera, setUseFrontCamera] = useState(false);

    // Audio refs
    const backgroundMusicRef = useRef(new Audio(backgroundMusic));
    const cameraSoundRef = useRef(new Audio(cameraSound));
    const scanSoundRef = useRef(new Audio(scanSound));

    // Set up background music
    useEffect(() => {
        const bgMusic = backgroundMusicRef.current;
        bgMusic.loop = true;
        bgMusic.volume = volume;

        return () => {
            bgMusic.pause();
            bgMusic.currentTime = 0;
        };
    }, []);

    const toggleMusic = () => {
        const bgMusic = backgroundMusicRef.current;
        if (isMusicPlaying) {
            bgMusic.pause();
        } else {
            bgMusic.play().catch(error => console.error('Error playing background music:', error));
        }
        setIsMusicPlaying(!isMusicPlaying);
    };

    const handleVolumeChange = (newVolume) => {
        setVolume(newVolume);
        const bgMusic = backgroundMusicRef.current;
        bgMusic.volume = newVolume;
        
        // If music was playing, ensure it continues playing
        if (isMusicPlaying && bgMusic.paused) {
            bgMusic.play().catch(error => console.error('Error resuming background music:', error));
        }
    };

    const lowerBackgroundVolume = () => {
        backgroundMusicRef.current.volume = volume * 0.4;
    };

    const restoreBackgroundVolume = () => {
        backgroundMusicRef.current.volume = volume;
    };

    const toggleCamera = async () => {
        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
        }
        setUseFrontCamera(!useFrontCamera);
        if (isCameraActive) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: !useFrontCamera ? "user" : "environment"
                    }
                });
                setVideoStream(stream);
            } catch (error) {
                console.error('Error switching camera:', error);
            }
        }
    };

    const handleToggleCameraPhoto = async () => {
        if (!isCameraActive) {
            setPokemonImage(null);
            setPredictedPokemon(null);
            setCapturedPhotoURL(null);
        }

        if (isCameraActive) {
            try {
                const mediaStreamTrack = videoStream.getVideoTracks()[0];
                const imageCapture = new ImageCapture(mediaStreamTrack);
                
                lowerBackgroundVolume();
                cameraSoundRef.current.currentTime = 0;
                await cameraSoundRef.current.play();
                setTimeout(restoreBackgroundVolume, 500);

                const photoBlob = await imageCapture.takePhoto();
                setCapturedPhoto(photoBlob);
                const photoURL = URL.createObjectURL(photoBlob);
                setCapturedPhotoURL(photoURL);
                setIsCameraActive(false);
                
                videoStream.getTracks().forEach(track => track.stop());
            } catch (error) {
                console.error('Error capturing photo:', error);
                restoreBackgroundVolume();
            }
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: useFrontCamera ? "user" : "environment"
                    }
                });
                setVideoStream(stream);
                setIsCameraActive(true);
            } catch (error) {
                console.error('Error starting camera:', error);
            }
        }
    };

    const handleDetectPokemon = async () => {
        if (capturedPhoto) {
            setIsLoading(true);
            setPokemonImage(null);
            setPredictedPokemon(null);
            
            lowerBackgroundVolume();
            scanSoundRef.current.currentTime = 0;
            scanSoundRef.current.loop = true;
            await scanSoundRef.current.play();

            const imageData = new FormData();
            imageData.append('image', capturedPhoto, 'photo.jpg');

            try {
                console.log('Sending image to backend...');
                const response = await fetch(`${API_URL}/upload-image`, {
                    method: 'POST',
                    body: imageData,
                    headers: { 'Accept': 'application/json' },
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log('Received response from backend:', data);

                    if (data.image) {
                        console.log('Setting captured photo URL...');
                        setCapturedPhotoURL(`data:image/jpeg;base64,${data.image}`);
                    }
                    
                    if (data.detected) {
                        console.log('Pokemon detected:', data.predicted_pokemon);
                        setPredictedPokemon(data.predicted_pokemon);

                        if (data.pokemon_image) {
                            console.log('Setting Pokemon image...');
                            const pokemonImageUrl = `data:image/png;base64,${data.pokemon_image}`;
                            setPokemonImage(pokemonImageUrl);
                        } else {
                            console.warn('No Pokemon image received from backend');
                        }
                    } else {
                        console.log('No Pokemon detected');
                        setPredictedPokemon("No Pokémon detected");
                    }
                } else {
                    console.error('Backend response not OK:', response.status);
                    setPredictedPokemon("No Pokémon detected");
                }
            } catch (error) {
                console.error('Error sending image to Flask app:', error);
                setPredictedPokemon("No Pokémon detected");
            } finally {
                scanSoundRef.current.pause();
                scanSoundRef.current.currentTime = 0;
                restoreBackgroundVolume();
                setIsLoading(false);
            }
        }
    };

    return (
        <div className="App">
            {/* Sound Controls */}
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
                {isCameraActive && (
                    <button 
                        className="sound-button"
                        onClick={toggleCamera}
                        title={useFrontCamera ? "Switch to Back Camera" : "Switch to Front Camera"}
                    >
                        {useFrontCamera ? "📱" : "🤳"}
                    </button>
                )}
            </div>

            {/* Decorative elements */}
            <div className="blue-light"></div>
            <div className="indicator-lights">
                <div className="light light-red"></div>
                <div className="light light-yellow"></div>
                <div className="light light-green"></div>
            </div>

            {/* Main screens */}
            <div className="left-screen">
                <div className="screen-overlay"></div>
                <div className="camera-container">
                    {isCameraActive ? (
                        <video
                            autoPlay
                            playsInline
                            muted
                            ref={(video) => {
                                if (video && videoStream) {
                                    video.srcObject = videoStream;
                                }
                            }}
                        />
                    ) : (
                        capturedPhotoURL && <img src={capturedPhotoURL} alt="Captured" />
                    )}
                    {isLoading && <div className="scanning"></div>}
                </div>
            </div>
            
            <div className="right-screen">
                <div className="screen-overlay"></div>
                <div className="screen-grid"></div>
                <div className="pokemon-result-container">
                    {predictedPokemon && (
                        <>
                            <div className="pokemon-label-wrapper">
                                <div className="pokemon-label">
                                    {predictedPokemon}
                                </div>
                            </div>
                            {pokemonImage && (
                                <div className="pokemon-image-container">
                                    <img 
                                        src={pokemonImage} 
                                        alt="Predicted Pokémon"
                                        className="pokemon-image"
                                        onLoad={() => console.log('Pokemon image loaded successfully')}
                                        onError={(e) => console.error('Error loading Pokemon image:', e)}
                                    />
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>

            <div className="buttons-container">
                <button onClick={handleToggleCameraPhoto} className="button">
                    {isCameraActive ? 'Take Photo' : 'Activate Camera'}
                </button>
                <button 
                    onClick={handleDetectPokemon} 
                    className="button"
                    disabled={!capturedPhotoURL || isLoading}
                >
                    Detect Pokémon
                </button>
            </div>
        </div>
    );
}

export default App;
