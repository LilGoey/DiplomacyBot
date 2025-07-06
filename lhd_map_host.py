# https://www.vdiplomacy.com/map.php?gameID=63956&turn=0&mapType=large

import requests
from PIL import Image

def download_map(game_id, turn, map_type='large', output_file='diplomacy_map.png'):
    # Construct the URL for the PNG image
    url = f'https://www.vdiplomacy.com/map.php?gameID={game_id}&turn={turn}&mapType={map_type}&fmapType=png'
    
    print(f'Downloading map from: {url}')
    resp = requests.get(url)
    
    if resp.status_code == 200 and resp.headers.get('Content-Type', '').startswith('image'):
        with open(output_file, 'wb') as f:
            f.write(resp.content)
        print(f'Map saved as {output_file}')
    else:
        print(f'Failed to download image: HTTP {resp.status_code}, Content-Type: {resp.headers.get("Content-Type")}')

    return output_file

def resize_with_padding(input_path, output_path, screen_width, screen_height, background_color=(0, 0, 0)):
    # Open original image in high quality mode
    img = Image.open(input_path).convert("RGBA")

    # Calculate scale to fit inside target while preserving aspect ratio
    scale = min(screen_width / img.width, screen_height / img.height)
    new_size = (int(img.width * scale), int(img.height * scale))

    # Resize with highest-quality resampling
    resized = img.resize(new_size, Image.Resampling.LANCZOS)

    # Create a padded background
    background = Image.new("RGBA", (screen_width, screen_height), background_color + (255,))

    # Center the resized image
    x = (screen_width - new_size[0]) // 2
    y = (screen_height - new_size[1]) // 2
    background.paste(resized, (x, y), resized)

    # Save to output PNG (lossless)
    background.save(output_path, format="PNG")
    print(f"Saved high-quality image to {output_path}")

if __name__ == '__main__':
    map = download_map(game_id=63956, turn=100, output_file=f"map{100}.png")
    resize_with_padding(map, output_path="map101.png", screen_width=1920, screen_height=540)

