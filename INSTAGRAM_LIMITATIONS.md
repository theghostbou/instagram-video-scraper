# Instagram Download Limitations

## Current Status
As of November 2025, Instagram has significantly strengthened their anti-scraping measures, making it very difficult to extract media URLs using server-side requests. The current implementation attempts multiple approaches but may not work for all Instagram posts.

## Why Downloads May Fail
- Instagram now serves different content to crawlers/bots than to real browsers
- Heavy reliance on client-side JavaScript rendering prevents server-side scraping
- Rate limiting and bot detection measures
- Anti-scraping measures have become more sophisticated

## Alternative Solutions
If the web-based downloader doesn't work for a specific post, consider these alternatives:

1. **Browser Extensions**: Use Instagram download extensions for Chrome/Firefox
2. **Mobile Apps**: Download dedicated Instagram media downloader apps
3. **Online Services**: Use established third-party online downloaders
4. **Selenium-based Tools**: Use browser automation tools that can render JavaScript

## Technical Details
The current implementation attempts:
- Multiple pattern matching for JSON data extraction
- Session management with realistic headers
- oEmbed API fallback
- Meta tag scanning
- Various header combinations to mimic real browsers

## Future Considerations
For production use, consider implementing a Selenium-based solution that can properly render the JavaScript content Instagram serves to browsers. This would require:
- Headless Chrome/Firefox browser
- Proper wait conditions for content loading
- JavaScript execution to access the rendered DOM