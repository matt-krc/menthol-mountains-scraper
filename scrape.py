import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import sys
from dateparser import parse
import time
import json

def get_older_posts_url(soup):
    older_posts = soup.find('a', string="Older Posts")
    if older_posts:
        return older_posts.get('href')
    else:
        return None


def check_if_blog_entry_title(link):
    try:
        parent = link.parent
        if 'post-title' in parent['class'] and 'entry-title' in parent['class']:
            return True
        return False
    except (AttributeError, KeyError):
        return False

def extrapolate_post_id(post):
    date_posts = post.parent.parent.find('h2', class_='date-header').find('span').decode_contents()
    return date_posts


url = 'http://mentholmountains.blogspot.com/'
res = requests.get(url)
soup = BeautifulSoup(res.content, 'html.parser')
links = soup.findAll('a')
older_posts_url = get_older_posts_url(soup)

ignore_domains = [
    'mentholmountains.blogspot.com',
    'www.blogger.com',
    'www.istockphoto.com',
    'googleusercontent.com',
    'blogger.googleusercontent.com',
    'draft.blogger.com'
]

data = {}
page = 1
while older_posts_url:
    print(f"On page: {page}")
    print(f"{url}")
    posts = soup.findAll('div', class_='post-outer')
    for post in posts:
        links = post.findAll('a')
        out_links = []
        imgs = []
        post_url = post_title = post_key = None
        for link in links:
            is_blog_entry_title = check_if_blog_entry_title(link)
            href = link.get('href')
            title = link.decode_contents()
            if is_blog_entry_title:
                post_url = href
                post_title = title
                post_key = ".".join(post_url.split("/")[-1].split(".")[:-1])
            else:
                o = urlparse(href)
                domain = o.netloc
                if domain == 'blogger.googleusercontent.com' and o.path.split('/')[1] == 'img':
                    # check for images
                    imgs.append(href)
                if domain in ignore_domains or not domain:
                    continue

                out_links.append({
                    'link': href,
                    'text': title
                })

        if post_key is not None:
            data[post_key] = {
                'url': post_url,
                'title': post_title,
                'links': out_links,
                'imgs': imgs
            }
        else:
            post_date = extrapolate_post_id(post)
            post_date_key = post_date.lower().replace(' ', '_').replace(',', '')
            post_date_url = f"http://mentholmountains.blogspot.com/{parse(post_date).strftime('%Y/%m')}/"
            n = 0
            while post_date_key in data:
                post_date_key += f'_{n}'
                n += 1
            data[post_date_key] = {
                'url': post_date_url,
                'title': post_date,
                'links': out_links,
                'imgs': imgs
            }

    url = older_posts_url
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    links = soup.findAll('a')
    older_posts_url = get_older_posts_url(soup)
    page += 1
    time.sleep(2)

with open('menthol_montains.json', 'w') as outf:
    json.dump(data, outf, indent=4)
