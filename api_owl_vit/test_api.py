import requests
import os

def test_api_root():
    # URL of the Cloud Run API endpoint
    base_url = 'https://owl-vit-api-150344248755.europe-west1.run.app'
    
    try:
        # Test different paths
        paths = ['', '/', '/health', '/detect']
        for path in paths:
            url = base_url + path
            print(f'\nTesting URL: {url}')
            response = requests.get(url)
            print(f'Status Code: {response.status_code}')
            print(f'Response: {response.text[:200]}')  # Print first 200 chars of response
        
    except requests.exceptions.RequestException as e:
        print(f'Error making request: {e}')
    except Exception as e:
        print(f'Error: {e}')

def test_detect_endpoint():
    # URL of the Cloud Run API endpoint
    url = 'https://owl-vit-api-150344248755.europe-west1.run.app/detect'
    
    # Get the absolute path to the image
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(os.path.dirname(current_dir), 'images', 'abra.png')
    
    print(f'\nTesting with image: {image_path}')
    print(f'Image exists: {os.path.exists(image_path)}')
    
    # Open the image file
    with open(image_path, 'rb') as f:
        # Create the files dictionary - using 'image' as the key to match the API expectation
        files = {'image': ('abra.png', f, 'image/png')}
        
        try:
            # Make the POST request with debug headers
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Python/3.9'
            }
            print('Making request to:', url)
            response = requests.post(url, files=files, headers=headers)
            
            # Print the response
            print('\nDetect Endpoint:')
            print('Status Code:', response.status_code)
            print('Response Headers:', dict(response.headers))
            if response.status_code == 200:
                result = response.json()
                print('Response:', result)
                print('\nDetection Results:')
                if 'boxes' in result:
                    for box, score, label in zip(result['boxes'], result['scores'], result['labels']):
                        text = result['text'][label]
                        print(f'- Detected "{text}" with confidence {score:.2f} at box {box}')
            else:
                print('Response:', response.text)
            
        except requests.exceptions.RequestException as e:
            print(f'Error making request: {e}')
        except Exception as e:
            print(f'Error: {e}')

if __name__ == '__main__':
    print("Testing API Root and Various Paths...")
    test_api_root()
    print("\nTesting Detect Endpoint...")
    test_detect_endpoint()
