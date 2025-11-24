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

        # Use a session with comprehensive headers to mimic a real browser and avoid detection
        session = requests.Session()

        # Try using Instagram Graph API with proper headers to bypass scraping detection
        graphql_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Instagram-AJAX': '1',
            'X-CSRFToken': '',
        }

        # First attempt: Try to get the page content with standard headers
        page_response = session.get(url, headers=graphql_headers, timeout=20)

        # If we get blocked or get a response that doesn't contain expected content, try alternative approaches
        if page_response.status_code != 200 or 'window._sharedData' not in page_response.text:
            # Second attempt: Try with different user agent to avoid detection
            mobile_headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }

            page_response = session.get(url, headers=mobile_headers, timeout=20)

            if page_response.status_code != 200 or 'window._sharedData' not in page_response.text:
                # Third attempt: Try with referer and different approach
                alt_headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'max-age=0',
                    'Referer': 'https://www.google.com/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'TE': 'Trailers',
                }

                page_response = session.get(url, headers=alt_headers, timeout=20)

        if page_response.status_code == 200:
            content = page_response.text

            # Look for the main JSON data in the page - Instagram often embeds this data
            # Try to find the main JSON payload in window._sharedData
            json_match = re.search(r'window\._sharedData\s*=\s*({.*?});', content)
            if not json_match:
                # Try the __additionalDataLoaded pattern
                json_match = re.search(r'window\.__additionalDataLoaded\s*\([^,]*,\s*({.*?})\s*\);', content, re.DOTALL)

            # If the standard patterns don't work, try looking for embedded JSON differently
            if not json_match:
                # Look for the main data object within a script tag
                script_match = re.search(r'<script[^>]*>\s*window\._sharedData\s*=\s*({.*?});\s*</script>', content, re.DOTALL)
                if script_match:
                    json_match = script_match

            if json_match:
                try:
                    json_data = json_match.group(1)
                    data = json.loads(json_data)

                    # Navigate to the media URL in the new Instagram structure
                    if 'entry_data' in data:
                        for key, value in data['entry_data'].items():
                            if isinstance(value, list) and len(value) > 0:
                                post_data = value[0]
                                if 'graphql' in post_data and 'shortcode_media' in post_data['graphql']:
                                    media = post_data['graphql']['shortcode_media']

                                    if media.get('__typename') == 'GraphVideo':
                                        # Video post
                                        video_url = media.get('video_url')
                                        if video_url:
                                            return video_url
                                        # Fallback to display URL for video thumbnails
                                        return media.get('display_url')
                                    elif media.get('__typename') == 'GraphImage':
                                        # Image post
                                        return media.get('display_url')
                                    elif media.get('__typename') == 'GraphSidecar':
                                        # Multiple media post - return first
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

            # If JSON parsing fails, try pattern matching in the content
            # Look for video URL
            video_match = re.search(r'"video_url":"([^"]+)"', content)
            if video_match:
                video_url = video_match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                return video_url

            # Look for image URL
            image_match = re.search(r'"display_url":"([^"]+)"', content)
            if image_match:
                image_url = image_match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                return image_url

            # Try more patterns for video URLs - sometimes they are in different formats
            more_video_patterns = [
                r'"video_versions".*?"url":"([^"]+)"',
                r'"url":"([^"]*\.mp4[^"]*)"',
                r'"playback_url":"([^"]+)"',
                r'"src":"([^"]*\.mp4[^"]*)"',
            ]

            for pattern in more_video_patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    video_url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                    return video_url

            # Try more patterns for images
            more_image_patterns = [
                r'"display_resources".*?"src":"([^"]+)"',
                r'"src":"([^"]*\.jpe?g[^"]*)"',
                r'"src":"([^"]*\.png[^"]*)"',
                r'"display_url":"([^"]+)"',
            ]

            for pattern in more_image_patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    image_url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                    return image_url

        # If the direct method doesn't work, try the oembed API
        oembed_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }

        oembed_url = f"https://api.instagram.com/oembed/?url={url}"
        oembed_response = session.get(oembed_url, headers=oembed_headers)

        if oembed_response.status_code == 200:
            try:
                oembed_data = oembed_response.json()

                # For videos, sometimes the direct media URL is available
                if 'url' in oembed_data and any(ext in oembed_data['url'] for ext in ['.mp4', '.mov', '.avi', '.m4v']):
                    return oembed_data['url']

                # For image posts or thumbnail of videos
                if 'thumbnail_url' in oembed_data:
                    return oembed_data['thumbnail_url']

            except json.JSONDecodeError:
                pass

        # Try direct GraphQL API request (this may require authentication but is worth trying)
        # Use the shortcode to make a direct API call to Instagram's GraphQL endpoint
        try:
            graphql_url = "https://www.instagram.com/graphql/query/"
            graphql_query = {
                "shortcode": shortcode,
                "child_comment_count": 3,
                "fetch_comment_count": 40,
                "parent_comment_count": 24,
                "has_threaded_comments": True
            }

            # Headers that try to mimic a real Instagram web request
            graphql_api_headers = {
                'X-IG-App-ID': '936619743392459',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': '*/*',
                'Referer': url,
            }

            response = session.post(
                graphql_url,
                headers=graphql_api_headers,
                data={'query_hash': 'b3055c01b4b222b87ee0b3894b2b3e2b', 'variables': json.dumps(graphql_query)},
                timeout=15
            )

            if response.status_code == 200:
                graphql_data = response.json()
                if 'data' in graphql_data and 'shortcode_media' in graphql_data['data']:
                    media = graphql_data['data']['shortcode_media']

                    if media.get('__typename') == 'GraphVideo':
                        video_url = media.get('video_url')
                        if video_url:
                            return video_url
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

        except Exception as e:
            print(f"GraphQL API request failed: {str(e)}")
            # Continue with other methods if GraphQL fails

        # If all else fails, try with different headers (to simulate different environments)
        # Some Instagram content might be accessible with different accept headers
        alt_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8,de;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/',
        }

        alt_response = session.get(url, headers=alt_headers, timeout=15)
        if alt_response.status_code == 200:
            content = alt_response.text

            # Look for meta tags that might contain the image/video URL
            meta_patterns = [
                r'<meta[^>]*property="og:video"[^>]*content="([^"]+)"',
                r'<meta[^>]*property="og:video:url"[^>]*content="([^"]+)"',
                r'<meta[^>]*property="og:video:secure_url"[^>]*content="([^"]+)"',
                r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"',
                r'<meta[^>]*name="twitter:image"[^>]*content="([^"]+)"',
                r'<meta[^>]*property="og:image:url"[^>]*content="([^"]+)"',
            ]

            for pattern in meta_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    media_url = match.group(1)
                    return media_url.replace('\\u0026', '&').replace('\\/', '/')

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