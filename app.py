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

        # Try multiple approaches with different headers to avoid detection
        headers_list = [
            # Desktop Chrome
            {
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
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.google.com/',
            },
            # Mobile Safari
            {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'no-cache',
            },
            # Desktop Firefox
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'TE': 'Trailers',
            },
            # Mac Chrome
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8,de;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Referer': 'https://www.google.com/',
            }
        ]

        # Try each header set in sequence
        for headers in headers_list:
            try:
                page_response = session.get(url, headers=headers, timeout=25)

                if page_response.status_code == 200 and 'window._sharedData' in page_response.text:
                    break
                elif page_response.status_code == 429:  # Rate limited
                    # Wait a bit before trying next header set
                    import time
                    time.sleep(2)
                    continue
            except requests.RequestException:
                # Try next header set
                continue

        if page_response.status_code == 200:
            content = page_response.text

            # Look for the main JSON data in the page - Instagram often embeds this data
            # Try to find the main JSON payload in window._sharedData
            json_match = re.search(r'window\._sharedData\s*=\s*({.*?});', content, re.DOTALL)
            if not json_match:
                # Try the __additionalDataLoaded pattern
                json_match = re.search(r'window\.__additionalDataLoaded\s*\([^,]*,\s*({.*?})\s*\);', content, re.DOTALL)

            # If the standard patterns don't work, try looking for embedded JSON differently
            if not json_match:
                # Look for the main data object within a script tag
                script_match = re.search(r'<script[^>]*>\s*window\._sharedData\s*=\s*({.*?});\s*</script>', content, re.DOTALL)
                if script_match:
                    json_match = script_match

            # Another possibility: Instagram's embedded JSON in different format
            if not json_match:
                json_match = re.search(r'({"config":.*?"is_vr_on_web":false})\s*,?\s*<\/script>', content, re.DOTALL)

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
            # Look for video URL with various patterns
            video_patterns = [
                r'"video_url":"([^"]+)"',
                r'"video_url":\s*"([^"]+)"',
                r'"video_versions".*?"url":"([^"]+)"',
                r'"url":"([^"]*\.mp4[^"]*)"',
                r'"playback_url":"([^"]+)"',
                r'"src":"([^"]*\.mp4[^"]*)"',
            ]

            for pattern in video_patterns:
                video_match = re.search(pattern, content, re.DOTALL)
                if video_match:
                    video_url = video_match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                    return video_url

            # Look for image URL patterns
            image_patterns = [
                r'"display_url":"([^"]+)"',
                r'"display_url":\s*"([^"]+)"',
                r'"display_resources".*?"src":"([^"]+)"',
                r'"src":"([^"]*\.jpe?g[^"]*)"',
                r'"src":"([^"]*\.png[^"]*)"',
            ]

            for pattern in image_patterns:
                image_match = re.search(pattern, content, re.DOTALL)
                if image_match:
                    image_url = image_match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                    return image_url

        # If the initial methods fail, try the oembed API
        oembed_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }

        try:
            oembed_url = f"https://api.instagram.com/oembed/?url={url}"
            oembed_response = session.get(oembed_url, headers=oembed_headers, timeout=15)

            if oembed_response.status_code == 200:
                oembed_data = oembed_response.json()

                # For videos, sometimes the direct media URL is available
                if 'url' in oembed_data and any(ext in oembed_data['url'] for ext in ['.mp4', '.mov', '.avi', '.m4v']):
                    return oembed_data['url']

                # For image posts or thumbnail of videos
                if 'thumbnail_url' in oembed_data:
                    return oembed_data['thumbnail_url']

        except (requests.RequestException, json.JSONDecodeError):
            pass

        # Try direct GraphQL API request with the Instagram App ID
        # This is another approach that may work in server environments
        try:
            graphql_url = "https://www.instagram.com/graphql/query/"

            # Different query hash for media extraction (these change often)
            query_hashes = [
                'b3055c01b4b222b87ee0b3894b2b3e2b',  # General media query
                '477b65a6628c505af9a3dc280c949596',  # Alternative query
                '9f8827793ef34641b2fb195d4d419b2d',  # Another alternative
            ]

            graphql_query = {
                "shortcode": shortcode,
                "child_comment_count": 3,
                "fetch_comment_count": 40,
                "parent_comment_count": 24,
                "has_threaded_comments": True
            }

            graphql_api_headers = {
                'X-IG-App-ID': '936619743392459',  # Instagram's web app client ID
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': '*/*',
                'Referer': url,
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': '',
            }

            # Try different query hashes
            for query_hash in query_hashes:
                try:
                    response = session.post(
                        graphql_url,
                        headers=graphql_api_headers,
                        data={'query_hash': query_hash, 'variables': json.dumps(graphql_query)},
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
                    elif response.status_code == 429:  # Rate limited
                        # Wait before trying next query hash
                        import time
                        time.sleep(1)
                        continue
                except requests.RequestException:
                    continue

        except Exception as e:
            print(f"GraphQL API request failed: {str(e)}")
            # Continue with other methods if GraphQL fails

        # Additional fallback: try using the URL with instagram.com/p/shortcode/ format
        try:
            # Create a direct URL to the media
            direct_url = f"https://www.instagram.com/p/{shortcode}/"

            # Try with a new session and different headers
            direct_session = requests.Session()
            direct_headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Referer': 'https://www.google.com/',
            }

            direct_response = direct_session.get(direct_url, headers=direct_headers, timeout=20)
            if direct_response.status_code == 200:
                content = direct_response.text

                # Look for media URLs in the direct URL response
                # Try more patterns for video URLs
                more_video_patterns = [
                    r'"video_url":"([^"]+)"',
                    r'"video_url":\s*"([^"]+)"',
                    r'"video_versions".*?"url":"([^"]+)"',
                    r'"url":"([^"]*\.mp4[^"]*)"',
                    r'"playback_url":"([^"]+)"',
                    r'"src":"([^"]*\.mp4[^"]*)"',
                ]

                for pattern in more_video_patterns:
                    video_match = re.search(pattern, content, re.DOTALL)
                    if video_match:
                        video_url = video_match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                        return video_url

                # Try more patterns for images
                more_image_patterns = [
                    r'"display_url":"([^"]+)"',
                    r'"display_url":\s*"([^"]+)"',
                    r'"display_resources".*?"src":"([^"]+)"',
                    r'"src":"([^"]*\.jpe?g[^"]*)"',
                    r'"src":"([^"]*\.png[^"]*)"',
                ]

                for pattern in more_image_patterns:
                    image_match = re.search(pattern, content, re.DOTALL)
                    if image_match:
                        image_url = image_match.group(1).replace('\\u0026', '&').replace('\\/', '/')
                        return image_url

                # Also check for meta tags in the direct response
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

        except Exception as e:
            print(f"Direct URL approach failed: {str(e)}")

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