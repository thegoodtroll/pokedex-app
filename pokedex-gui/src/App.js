import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import LoadingScreen from './components/LoadingScreen';
import PokemonSpeaker from './components/PokemonSpeaker';
import cameraSound from './assets/camera.mp3';
import scanSound from './assets/scan.mp3';
import backgroundMusic from './assets/cerulean-city.wav';

// Define your Flask backend URL here
const API_URL = "https://flask-backend-150344248755.europe-west1.run.app";

function App() {
    const [capturedPhoto, setCapturedPhoto] = useState(null);
    const [capturedPhotoURL, setCapturedPhotoURL] = useState(null);
    const [predictedPokemon, setPredictedPokemon] = useState(null);
    const [pokemonImage, setPokemonImage] = useState(null);
    const [videoStream, setVideoStream] = useState(null);  
    const [isCameraActive, setIsCameraActive] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isMusicPlaying, setIsMusicPlaying] = useState(true);
    const [volume, setVolume] = useState(0.3);
    const [showVolumeSlider, setShowVolumeSlider] = useState(false);
    const [useFrontCamera, setUseFrontCamera] = useState(false);
    const [isInitializing, setIsInitializing] = useState(true);
    const [cameraError, setCameraError] = useState(null);

    // Audio refs
    const backgroundMusicRef = useRef(new Audio(backgroundMusic));
    const cameraSoundRef = useRef(new Audio(cameraSound));
    const scanSoundRef = useRef(new Audio(scanSound));

    // Initialize backend on load
    useEffect(() => {
        const warmupBackend = async () => {
            try {
                // Try the health-check endpoint first
                const response = await fetch(`${API_URL}/health-check`);
                if (response.ok) {
                    setIsInitializing(false);
                    return;
                }

                // If health-check fails, try the api/health endpoint
                const apiResponse = await fetch(`${API_URL}/api/health`);
                if (apiResponse.ok) {
                    setIsInitializing(false);
                    return;
                }

                // If both fail, try the main endpoint
                const mainResponse = await fetch(API_URL);
                if (mainResponse.ok) {
                    setIsInitializing(false);
                }
            } catch (error) {
                console.error('Error warming up backend:', error);
                // Still hide loading screen after a timeout even if there's an error
                setTimeout(() => setIsInitializing(false), 3000);
            }
        };

        warmupBackend();
    }, []);

    // Set up background music
    useEffect(() => {
        const bgMusic = backgroundMusicRef.current;
        bgMusic.loop = true;
        bgMusic.volume = volume;
        
        // Auto-play background music immediately after user interaction
        const playMusic = () => {
            bgMusic.play()
                .then(() => {
                    document.removeEventListener('click', playMusic);
                })
                .catch(error => console.error('Error playing background music:', error));
        };

        playMusic(); // Try to play immediately
        document.addEventListener('click', playMusic); // Also try on first click

        return () => {
            bgMusic.pause();
            bgMusic.currentTime = 0;
            document.removeEventListener('click', playMusic);
        };
    }, [volume]);

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
        backgroundMusicRef.current.volume = volume * 0.1;
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
                setCameraError(null);
            } catch (error) {
                console.error('Error switching camera:', error);
                setCameraError("Failed to switch camera. Please check your camera permissions.");
                setIsCameraActive(false);
            }
        }
    };

    const handleToggleCameraPhoto = async () => {
        if (!isCameraActive) {
            setPokemonImage(null);
            setPredictedPokemon(null);
            setCapturedPhotoURL(null);
            setCameraError(null);
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
                setCameraError("Failed to capture photo. Please try again.");
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
                setCameraError(null);
            } catch (error) {
                console.error('Error starting camera:', error);
                setCameraError("Failed to access camera. Please check your camera permissions and ensure no other app is using the camera.");
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

    if (isInitializing) {
        return <LoadingScreen 
            isMusicPlaying={isMusicPlaying}
            toggleMusic={toggleMusic}
            volume={volume}
            handleVolumeChange={handleVolumeChange}
            showVolumeSlider={showVolumeSlider}
            setShowVolumeSlider={setShowVolumeSlider}
        />;
    }

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
                    {cameraError && (
                        <div className="camera-error">
                            {cameraError}
                        </div>
                    )}
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
                            <div className="pokemon-image-container">
                                {pokemonImage && (
                                    <img 
                                        src={pokemonImage} 
                                        alt="Predicted Pokémon"
                                        className="pokemon-image"
                                        onLoad={() => console.log('Pokemon image loaded successfully')}
                                        onError={(e) => console.error('Error loading Pokemon image:', e)}
                                    />
                                )}
                            </div>
                            <PokemonSpeaker 
                                pokemonName={predictedPokemon}
                                isActive={predictedPokemon && predictedPokemon !== "No Pokémon detected"}
                                onStartSpeak={lowerBackgroundVolume}
                                onEndSpeak={restoreBackgroundVolume}
                            />
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
