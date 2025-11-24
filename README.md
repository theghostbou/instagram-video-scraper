# InstaSave - Instagram Video & Photo Downloader

A Flask-based web application that allows users to download Instagram videos and photos by providing the post URL.

## Features

- Download Instagram videos and photos
- Responsive, mobile-friendly design
- Clean, modern UI with gradient background
- Fast processing
- Works on all devices and platforms

## Prerequisites

- Python 3.7+
- pip (Python package installer)

## Installation

1. Clone or download this repository
2. Navigate to the project directory
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask application:
   ```bash
   python app.py
   ```
   
2. Open your browser and go to `http://localhost:5001`

3. Paste an Instagram post URL in the input field and click "Download"

4. View and download the media content

Alternatively, you can use the run script:
```bash
chmod +x run.sh
./run.sh
```

## Project Structure

```
.
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
├── README.md             # This file
├── run.sh                # Run script
├── install.py            # Installation script
├── test_app.py           # Test script
├── templates/            # HTML templates
│   └── index.html
└── static/               # Static assets
    ├── css/
    │   └── style.css
    ├── js/
    │   └── script.js
    └── images/
```

## Technologies Used

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript (ES6)
- **Styling**: CSS with Flexbox and Grid for responsive design
- **API**: Instagram oEmbed API and web scraping techniques

## How It Works

1. User provides an Instagram post URL
2. The backend extracts the media URL using Instagram's API and web scraping techniques
3. The frontend displays the media and provides a download link

## Important Notice

This tool is intended for personal use only. Please respect Instagram's Terms of Service and the rights of content creators. Make sure you have permission to download any content you access through this tool.

Instagram and the Instagram logo are trademarks of Instagram, LLC.

## License

This project is for educational purposes only.