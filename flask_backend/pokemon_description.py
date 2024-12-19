import os
import requests
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class PokemonDescriptionService:
    def __init__(self):
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        self.voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')  # Default to Adam voice
        
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")

    def get_pokemon_description(self, pokemon_name: str) -> Optional[str]:
        """Get a description of the Pokémon using OpenRouter API"""
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            # Required headers for OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000, https://pokedex-1hlc.onrender.com",
                "X-Title": "Pokedex App"
            }
            
            # Use model from environment variable or default
            model = os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini-2024-07-18')
            
            # System prompt as a constant
            system_prompt = """VIGTIGT: DU SKAL ALTID SVARE PÅ DANSK! ALDRIG PÅ ENGELSK!

Du er en dansk talende Pokedex-assistent, en vidende og venlig guide, der giver detaljeret, engagerende og præcis information om Pokémon. Dine svar skal være tilpasset både begyndere og lettere erfarne Pokémon-trænere og balancere tekniske detaljer med letforståelige forklaringer.

Når du bliver spurgt om en Pokémon ved navn, skal du følge denne struktur i dit svar:
1. Start med Pokémonens navn efterfulgt af et udråbstegn
2. Beskriv dens type(r) og udseende
3. Nævn dens habitat
4. Beskriv dens evner og særlige træk
5. Nævn dens udviklingsstadier (brug aldrig ordet 'evolution')

REGLER:
- Svar ALTID på dansk
- Hold svarene KORTE og PRÆCISE
- Brug ALDRIG punktform
- Brug ALDRIG ordet 'evolution' - brug 'udvikling' i stedet
- Giv IKKE meta-information om Pokémon-universet
- Brug en entusiastisk og vidende tone

HUSK: DU MÅ KUN SVARE PÅ DANSK!"""
            
            # Craft the user prompt in Danish with explicit language instruction
            user_prompt = f"""
            BESVAR KUN PÅ DANSK!
            Beskriv Pokémonen {pokemon_name} på dansk.
            Følg nøje systemets instruktioner for formatering og indhold.
            """.strip()
            
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 1,
                "max_tokens": 0,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "stop": ["In English:", "English translation:", "Translated:"]
            }
            
            # Debug: Print complete request data
            print("\nDEBUG - Complete Request Data:")
            print("-" * 50)
            print("URL:", url)
            print("\nHeaders:")
            safe_headers = headers.copy()
            safe_headers['Authorization'] = '[REDACTED]'
            print(json.dumps(safe_headers, indent=2))
            print("\nRequest Body:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("-" * 50)
            
            response = requests.post(url, headers=headers, json=data)
            
            # Debug: Print response details
            print("\nDEBUG - Response Status Code:", response.status_code)
            print("DEBUG - Response Headers:")
            print(json.dumps(dict(response.headers), indent=2))
            
            response.raise_for_status()
            response_data = response.json()
            
            # Debug: Print complete response
            print("\nDEBUG - Complete Response:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            description = response_data['choices'][0]['message']['content'].strip()
            
            # Verify Danish content
            danish_words = ["er", "og", "i", "på", "med", "som", "den", "det", "en", "et"]
            has_danish = any(word in description.lower() for word in danish_words)
            if not has_danish:
                print("\nWARNING: Response might not be in Danish!")
                print("Response:", description)
            
            return description
            
        except Exception as e:
            print(f"\nDEBUG - Error getting Pokémon description: {str(e)}")
            if isinstance(e, requests.exceptions.HTTPError):
                print("DEBUG - Error Response Content:")
                print(e.response.text)
            return None

    def get_audio_stream(self, text: str) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs API"""
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_flash_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.5,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return None
