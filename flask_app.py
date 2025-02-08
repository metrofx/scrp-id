# flask_app.py
from flask import Flask, request, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, unquote

app = Flask(__name__)

# [Previous scraping functions remain the same...]
# Copy all the scraping functions here: scrape_detik(), scrape_kompas(), process_paragraphs(), scrape_article()

def extract_url(text):
    """Extract URL from text that might contain other content"""
    # Common URL patterns
    url_patterns = [
        # Standard URL pattern
        r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*',
        # Common messenger URL pattern (when URL is at start or end)
        r'(?:^|\s)(?:https?://)?(?:www\.)?(?:detik\.com|kompas\.com)/\S+',
        # search.app URLs
        r'https?://(?:www\.)?search\.app/\S+'
    ]

    for pattern in url_patterns:
        urls = re.findall(pattern, text)
        if urls:
            # Return the first found URL
            url = urls[0].strip()
            # Add https:// if missing
            if not url.startswith('http'):
                url = 'https://' + url
            return url

    return None

def follow_redirect(url):
    """Follow redirects and return the final URL"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'}
        # Allow redirects and get the response
        response = requests.get(url, headers=headers, allow_redirects=True)
        # Return the final URL after redirects
        return response.url, response
    except Exception as e:
        return None, None

def scrape_detik(soup):
    content = soup.find('div', class_='detail__body-text')
    if not content:
        return "Could not find article content"

    paragraphs = content.find_all('p')
    skip_phrases = [
        'baca juga', 'baca:', 'baca :', 'advertisement',
        'advertisement scroll', 'simak video', 'simak selengkapnya',
        'scroll to continue with content', 'simak juga',
        'scroll to resume content', 'lihat juga video'
    ]

    return process_paragraphs(paragraphs, skip_phrases)

def scrape_kompas(soup):
    content = soup.find('div', class_='read__content')
    if not content:
        return "Could not find article content"

    paragraphs = content.find_all('p')
    skip_phrases = ['baca juga', 'baca:', 'baca :']

    return process_paragraphs(paragraphs, skip_phrases)

def process_paragraphs(paragraphs, skip_phrases):
    cleaned_paragraphs = []
    for p in paragraphs:
        text = p.get_text().strip()
        if text:
            if not any(phrase in text.lower() for phrase in skip_phrases):
                text = re.sub(r'\s+', ' ', text)
                if text.strip():
                    cleaned_paragraphs.append(text)

    return '\n\n'.join(cleaned_paragraphs)

def scrape_og_tags(soup):
    og_tags = {}
    for tag in soup.find_all('meta', property=re.compile(r'^og:')):
        og_tags[tag.get('property')] = tag.get('content')
    return og_tags

def scrape_article(input_text):
    try:
        # Extract URL from input text
        url = extract_url(input_text)
        if not url:
            return "No valid URL found in the input"

        # Check if it's a search.app URL
        # if 'search.app' in url:
        #     final_url, response = follow_redirect(url)
        #     if not final_url:
        #         return "Error following redirect"
        #     url = final_url  # Use the final URL for further processing
        else:
            # Regular URL handling
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        domain = urlparse(url).netloc.lower()

        # Log the final URL for debugging
        print(f"Processing URL: {url}")
        print(f"Detected domain: {domain}")

        content = ""
        if 'detik.com' in domain:
            content = scrape_detik(soup)
        elif 'kompas.com' in domain:
            content = scrape_kompas(soup)
        else:
            content = f"Unsupported news site. Currently supporting: detik.com, kompas.com\nFinal URL: {url}"

        og_tags = scrape_og_tags(soup)
        return {'content': content, 'og_tags': og_tags}

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def home():
    url = request.args.get('url')
    og_tags = {}

    if url:
        # Fetch metadata if a URL is provided
        result = scrape_article(url)
        if isinstance(result, dict):
            og_tags = result.get('og_tags', {})

    return render_template('index.html', og_tags=og_tags)

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if request.method == 'POST':
        url = request.json.get('url')
    else:
        url = request.args.get('url')
        if url:
            url = unquote(url)

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    result = scrape_article(url)

    # Handle both dictionary and string responses
    if isinstance(result, dict):
        content = result.get('content', '')
        og_tags = result.get('og_tags', {})
    else:
        content = str(result)
        og_tags = {}

    if request.method == 'POST':
        return jsonify({'content': content, 'og_tags': og_tags})
    else:
        return render_template('index.html', content=content, url=url, og_tags=og_tags)

# No need for if __name__ == '__main__' block in production
