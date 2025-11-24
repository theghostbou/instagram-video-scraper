from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import re
from urllib.parse import urlparse
import os
import json
from config import Config

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(Config)
CORS(app)

def extract_instagram_media_url(url):
    """
    Extract media URL from Instagram post URL using multiple approaches
    """
    try:
        # Parse the Instagram URL to get the shortcode
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        # The shortcode is the identifier in the URL
        shortcode = None
        for i, part in enumerate(path_parts):
            if part in ['p', 'reel', 'tv', 'reels'] and i + 1 < len(path_parts):
                shortcode = path_parts[i + 1]
                # Extract just the shortcode part (sometimes there are extra parameters)
                shortcode = shortcode.split('?')[0].split('/')[0]
                break

        if not shortcode:
            # Try to find it directly as the last part if it's a simple URL
            if len(path_parts) > 0 and len(path_parts[-1]) > 0:
                shortcode = path_parts[-1].split('?')[0]

        if not shortcode:
            return None

        # New approach: Instagram changed security measures significantly
        # Using a different approach that handles modern Instagram security
        session = requests.Session()

        # First, get a valid session cookie by accessing the main Instagram page
        try:
            initial_response = session.get("https://www.instagram.com/", timeout=10)
        except:
            pass  # If we can't get the initial page, continue with the request

        # Use updated headers with more realistic values and session management
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }

        # Try to get the page with a delay to make it seem more human-like
        import time
        time.sleep(1)  # Small delay to make it seem more like a human request

        page_response = session.get(url, headers=headers, timeout=30)

        if page_response.status_code == 200:
            content = page_response.text

            # Try to find embedded JSON data in the page
            # Modern Instagram uses different patterns
            json_match = None
            patterns = [
                r'window\.__additionalDataLoaded\s*\([^,]*,\s*({.*?})\s*\);',
                r'window\._sharedData\s*=\s*({.*?});',
                r'({"config":.*?"is_vr_on_web":false})\s*,?\s*<\/script>',
            ]

            for pattern in patterns:
                json_match = re.search(pattern, content, re.DOTALL)
                if json_match:
                    break

            if json_match:
                try:
                    json_data = json_match.group(1)
                    data = json.loads(json_data)

                    # Navigate the modern Instagram data structure
                    if 'entry_data' in data:
                        for key, value in data['entry_data'].items():
                            if isinstance(value, list) and len(value) > 0:
                                for post_data in value:
                                    if 'graphql' in post_data and 'shortcode_media' in post_data['graphql']:
                                        media = post_data['graphql']['shortcode_media']

                                        if media.get('__typename') == 'GraphVideo':
                                            video_url = media.get('video_url')
                                            if video_url:
                                                return video_url
                                            # Fallback to display URL for video thumbnails
                                            return media.get('display_url')
                                        elif media.get('__typename') == 'GraphImage':
                                            return media.get('display_url')
                                        elif media.get('__typename') == 'GraphSidecar':
                                            edges = media.get('edge_sidecar_to_children', {}).get('edges', [])
                                            if edges:
                                                first_media = edges[0]['node']
                                                if first_media.get('__typename') == 'GraphVideo':
                                                    video_url = first_media.get('video_url')
                                                    if video_url:
                                                        return video_url
                                                    return first_media.get('display_url')
                                                else:
                                                    return first_media.get('display_url')

                except (json.JSONDecodeError, KeyError, AttributeError) as e:
                    print(f"JSON parsing error: {str(e)}")
                    pass

            # Pattern extraction for videos and images in modern Instagram
            # More comprehensive pattern matching
            patterns = [
                r'"video_url":"([^"]+)"',
                r'"video_versions":\s*\[([^\]]+)\]',
                r'"url":"([^"]*\.mp4[^"]*)"',
                r'"display_url":"([^"]+)"',
                r'"src":"([^"]*\.mp4[^"]*)"',
                r'"src":"([^"]*\.jpg[^"]*)"',
                r'"src":"([^"]*\.png[^"]*)"',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # If it's a video_versions array, extract the URL from it
                    if pattern == r'"video_versions":\s*\[([^\]]+)\]':
                        url_match = re.search(r'"url":"([^"]+)"', match)
                        if url_match:
                            video_url = url_match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                            if '.mp4' in video_url:
                                return video_url
                    else:
                        media_url = match.replace('\\u0026', '&').replace('\\/', '/')
                        return media_url

        # Fallback: Try using Instagram's oembed API
        try:
            import urllib.parse
            encoded_url = urllib.parse.quote(url, safe=':/?#[]@!$&\'()*+,;=')
            oembed_url = f"https://api.instagram.com/oembed/?url={encoded_url}"

            oembed_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }

            oembed_response = session.get(oembed_url, headers=oembed_headers, timeout=20)
            if oembed_response.status_code == 200:
                oembed_data = oembed_response.json()

                # Check for media in oembed data
                if 'url' in oembed_data and any(ext in oembed_data['url'] for ext in ['.mp4', '.mov', '.avi', '.m4v']):
                    return oembed_data['url']
                elif 'thumbnail_url' in oembed_data:
                    return oembed_data['thumbnail_url']
        except:
            pass

        # For server environments, sometimes we need to try a different approach
        # Try to extract using a CDN or proxy-like method by constructing direct URLs
        # This works in some cases but may need specific server configuration
        try:
            # Try to access media directly using shortcode
            direct_media_url = f"https://www.instagram.com/p/{shortcode}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8,de;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }

            response = session.get(direct_media_url, headers=headers, timeout=25)
            if response.status_code == 200:
                content = response.text

                # Search for media URLs in this page
                media_patterns = [
                    r'"video_url":"([^"]+)"',
                    r'"display_url":"([^"]+)"',
                    r'"src":"([^"]*\.mp4[^"]*)"',
                    r'"src":"([^"]*\.jpe?g[^"]*)"',
                ]

                for pattern in media_patterns:
                    match = re.search(pattern, content)
                    if match:
                        media_url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                        return media_url

                # Look for meta tags in the response
                meta_patterns = [
                    r'<meta[^>]*property="og:video"[^>]*content="([^"]+)"',
                    r'<meta[^>]*property="og:video:url"[^>]*content="([^"]+)"',
                    r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"',
                    r'<meta[^>]*property="og:image:url"[^>]*content="([^"]+)"',
                ]

                for pattern in meta_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        media_url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                        return media_url
        except:
            pass

        # Last resort: Try with a referer that looks like it's coming from Instagram
        try:
            headers_with_referer = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.instagram.com/',
                'X-Requested-With': 'XMLHttpRequest',
                'X-Instagram-AJAX': '1',
                'X-CSRFToken': '',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }

            page_response = session.get(url, headers=headers_with_referer, timeout=30)
            if page_response.status_code == 200:
                content = page_response.text

                # Extract media from this response
                patterns = [
                    r'"video_url":"([^"]+)"',
                    r'"display_url":"([^"]+)"',
                    r'"src":"([^"]*\.mp4[^"]*)"',
                    r'"src":"([^"]*\.jpe?g[^"]*)"',
                ]

                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        media_url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                        return media_url
        except:
            pass

        return None
    except Exception as e:
        print(f"Error extracting Instagram media: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Validate Instagram URL
        if 'instagram.com' not in url.lower() and 'instagr.am' not in url.lower():
            return jsonify({'error': 'Please enter a valid Instagram URL'}), 400

        media_url = extract_instagram_media_url(url)

        if not media_url:
            return jsonify({'error': 'Could not extract media from this URL. Instagram has implemented anti-scraping measures that may prevent downloads. Try using a desktop browser extension or a dedicated Instagram downloader tool.'}), 400

        return jsonify({
            'success': True,
            'media_url': media_url,
            'media_type': 'video' if any(ext in media_url.lower() for ext in ['.mp4', '.mov', '.avi', '.mkv', '.m4v']) else 'image'
        })

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)