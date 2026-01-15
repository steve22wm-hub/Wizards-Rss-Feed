#!/usr/bin/env python3
"""
Washington Post Wizards RSS Feed Generator
Scrapes the WaPo Wizards page and generates an RSS feed
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys

def fetch_wizards_articles():
    """Fetch and parse articles from the Washington Post Wizards page"""
    url = "https://www.washingtonpost.com/sports/wizards/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    
    # Look for article links - WaPo typically uses specific classes or data attributes
    # We'll try multiple selectors to be robust
    article_links = []
    
    # Try finding articles by common WaPo patterns
    # Pattern 1: Links within article elements
    article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and ('story' in x.lower() or 'article' in x.lower() or 'card' in x.lower()))
    for element in article_elements:
        link = element.find('a', href=True)
        if link and '/sports/' in link['href']:
            article_links.append(link)
    
    # Pattern 2: Direct links to article pages
    if not article_links:
        all_links = soup.find_all('a', href=True)
        article_links = [link for link in all_links if '/sports/202' in link.get('href', '') or '/sports/wizards/' in link.get('href', '')]
    
    seen_urls = set()
    
    for link in article_links[:20]:  # Limit to most recent 20 articles
        href = link.get('href', '')
        
        # Make sure URL is absolute
        if href.startswith('/'):
            href = 'https://www.washingtonpost.com' + href
        
        # Skip duplicates and non-article URLs
        if href in seen_urls or 'washingtonpost.com/sports' not in href:
            continue
        
        # Skip if it's just the main page
        if href.rstrip('/') == url.rstrip('/'):
            continue
            
        seen_urls.add(href)
        
        # Extract title
        title = link.get_text(strip=True)
        if not title or len(title) < 10:  # Skip if title is too short
            # Try to find title in nearby elements
            parent = link.find_parent(['article', 'div'])
            if parent:
                heading = parent.find(['h1', 'h2', 'h3', 'h4'])
                if heading:
                    title = heading.get_text(strip=True)
        
        if not title or len(title) < 10:
            continue
        
        # Try to find description
        description = ""
        parent = link.find_parent(['article', 'div'])
        if parent:
            desc_element = parent.find(['p', 'div'], class_=lambda x: x and ('dek' in x.lower() or 'excerpt' in x.lower() or 'summary' in x.lower()))
            if desc_element:
                description = desc_element.get_text(strip=True)
        
        # Try to find publication date
        pub_date = None
        if parent:
            time_element = parent.find('time')
            if time_element:
                datetime_attr = time_element.get('datetime')
                if datetime_attr:
                    try:
                        pub_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    except:
                        pass
        
        if not pub_date:
            pub_date = datetime.now()
        
        articles.append({
            'title': title,
            'link': href,
            'description': description if description else title,
            'pub_date': pub_date
        })
    
    return articles

def generate_rss_feed(articles, output_file='wizards_feed.xml'):
    """Generate RSS 2.0 feed from articles"""
    
    # Create RSS structure
    rss = ET.Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    
    channel = ET.SubElement(rss, 'channel')
    
    # Channel metadata
    ET.SubElement(channel, 'title').text = 'Washington Post - Wizards'
    ET.SubElement(channel, 'link').text = 'https://www.washingtonpost.com/sports/wizards/'
    ET.SubElement(channel, 'description').text = 'Latest Washington Wizards news from The Washington Post'
    ET.SubElement(channel, 'language').text = 'en-us'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    # Add items
    for article in articles:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = article['title']
        ET.SubElement(item, 'link').text = article['link']
        ET.SubElement(item, 'description').text = article['description']
        ET.SubElement(item, 'pubDate').text = article['pub_date'].strftime('%a, %d %b %Y %H:%M:%S +0000')
        ET.SubElement(item, 'guid').text = article['link']
    
    # Pretty print XML
    xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent="  ")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"RSS feed generated successfully: {output_file}")
    print(f"Found {len(articles)} articles")

def main():
    print("Fetching Washington Post Wizards articles...")
    articles = fetch_wizards_articles()
    
    if not articles:
        print("Warning: No articles found. The page structure may have changed.")
        print("Generating empty feed...")
    
    generate_rss_feed(articles)

if __name__ == "__main__":
    main()
