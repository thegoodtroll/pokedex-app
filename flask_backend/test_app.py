import requests
import os
import sys

def test_upload_image():
    try:
        # URL of the Flask app endpoint
        url = 'http://localhost:5000/upload-image'
        
        # Get the absolute path to the image
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(os.path.dirname(current_dir), 'images', 'abra.png')
        
        print(f'\nTesting with image: {image_path}')
        print(f'Image exists: {os.path.exists(image_path)}')
        
        if not os.path.exists(image_path):
            print(f"Error: Image file not found at {image_path}")
            return

        # Open the image file
        with open(image_path, 'rb') as f:
            # Create the files dictionary
            files = {'image': ('abra.png', f, 'image/png')}
            
            try:
                # Make the POST request
                print('Making request to:', url)
                response = requests.post(url, files=files)
                
                # Print the response
                print('\nUpload Image Endpoint:')
                print('Status Code:', response.status_code)
                if response.status_code == 200:
                    result = response.json()
                    print('\nResponse:')
                    print('Detected:', result.get('detected'))
                    print('Predicted Pokemon:', result.get('predicted_pokemon'))
                    print('Pokemon image included:', bool(result.get('pokemon_image')))
                else:
                    print('Response:', response.text)
                
            except requests.exceptions.ConnectionError as e:
                print(f'Connection Error: Make sure Flask app is running on {url}')
                print(f'Error details: {e}')
            except requests.exceptions.RequestException as e:
                print(f'Error making request: {e}')
            except Exception as e:
                print(f'Unexpected error: {e}')
                print(f'Error type: {type(e)}')
                print(f'Error details: {str(e)}')
    except Exception as e:
        print(f'Test script error: {e}')
        print(f'Python version: {sys.version}')
        print(f'Current working directory: {os.getcwd()}')

if __name__ == '__main__':
    print("Starting test...")
    test_upload_image()
