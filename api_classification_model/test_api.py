import requests
import os

def test_health():
    url = 'http://localhost:8080/health'
    print(f'\nTesting health endpoint: {url}')
    
    try:
        response = requests.get(url)
        print('Status Code:', response.status_code)
        print('Response:', response.json())
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')

def test_classify():
    url = 'http://localhost:8080/classify'
    
    # Get the absolute path to the test image
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(os.path.dirname(current_dir), 'images', 'abra.png')
    
    print(f'\nTesting with image: {image_path}')
    print(f'Image exists: {os.path.exists(image_path)}')
    
    # Open the image file
    with open(image_path, 'rb') as f:
        # Create the files dictionary
        files = {'image': ('abra.png', f, 'image/png')}
        
        try:
            # Make the POST request
            print('Making request to:', url)
            response = requests.post(url, files=files)
            
            # Print the response
            print('\nClassify Endpoint:')
            print('Status Code:', response.status_code)
            print('Response:', response.json() if response.status_code == 200 else response.text)
            
        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')

if __name__ == '__main__':
    print("Testing Classification API...")
    test_health()
    test_classify()
