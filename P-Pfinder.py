from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin

app = Flask(__name__)

def get_domain_links(domain):
    archive_url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=text&fl=original&collapse=urlkey"
    response = requests.get(archive_url)
    if response.status_code == 200:
        domain_links = response.text.split("\n")
        return domain_links
    return None

def extract_unique_links(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        for tag in soup.select('a[href], link[href], img[src], script[src], iframe[src]'):
            href = tag.get('href') or tag.get('src')
            if href:
                absolute_href = urljoin(url, href)
                links.add(absolute_href)
        return list(links)
    return None

def get_unique_paths(links):
    unique_paths = set()
    for link in links:
        parsed_link = urlparse(link)
        unique_paths.add(parsed_link.path)
    return list(unique_paths)

def get_all_paths_or_params(domain, extract_paths=True):
    domain_links = get_domain_links(domain)
    if domain_links:
        data = set()
        for link in domain_links:
            parsed_link = urlparse(link)
            if extract_paths:
                data.add(parsed_link.path)
            elif parsed_link.query:
                data.update(parsed_link.query.split('&'))
        return list(data)
    return None

@app.route('/extract-links', methods=['GET'])
def handle_extract_links():
    all_param = request.args.get('all')
    if all_param and all_param.lower() == 'true':
        domain = request.args.get('domain')
        url = request.args.get('url')
        if domain or url:
            data = {}
            if domain:
                data['paths'] = get_all_paths_or_params(domain, extract_paths=True)
                data['params'] = get_all_paths_or_params(domain, extract_paths=False)
            elif url:
                data['paths'] = get_unique_paths(extract_unique_links(url))
                data['params'] = get_all_paths_or_params(url, extract_paths=False)
            if data['paths'] is not None and data['params'] is not None:
                return jsonify(data)
            return jsonify({"error": "Failed to retrieve paths and/or params."}), 404
        return jsonify({"error": "Domain or URL parameter is missing."}), 400
    return jsonify({"error": "All parameter is missing or not set to true."}), 400

if __name__ == '__main__':
    app.run(debug=True)
