import praw
from bs4 import BeautifulSoup
import requests
import re
import os
import glob
import sys

COUNT = 0
MIN_SCORE = 100
imgurUrlPattern = re.compile(r'(http://i.imgur.com/(.*))(\?.*)?')


def downloadImage(img_url, local_file_name):
    global COUNT
    resp = requests.get(img_url)
    if resp.status_code == 200:
        COUNT += 1
        print('Downloading %s...' % (local_file_name))
    else:
        print(resp.status_code)
    with open(local_file_name, 'wb') as fo:
        for chunk in resp.iter_content(4096):
            fo.write(chunk)


def get_posts(target_sub):
    submissions = target_sub.get_top_from_all(limit=2000)
    for post in submissions:
        # Check for all cases where we will skip a post
        # skip non-imgur posts
        if "imgur.com/" not in post.url:
            continue
        '''
        if post.score < MIN_SCORE:
            continue
        '''
        # skip posts where files have already been downloaded
        if len(glob.glob('reddit_%s_*' % (post.id))) > 0:
            continue
        # Handle album submissions.
        if 'http://imgur.com/a/' in post.url:
            album_id = post.url[len('http://imgur.com/a/'):]
            htmlSource = requests.get(post.url).text
            soup = BeautifulSoup(htmlSource)
            matches = soup.select('.album-view-image-link a')
            for match in matches:
                img_url = match['href']
                if '?' in img_url:
                    img_file = img_url[img_url.rfind('/')
                                       + 1:img_url.rfind('?')]
                else:
                    img_file = img_url[img_url.rfind('/') + 1:]
                local_file_name = 'reddit_%s_%s_album_%s_imgur_%s' %\
                                    (target_sub, post.id, album_id, img_file)
                downloadImage('http:' + match['href'], local_file_name)
        elif 'http://i.imgur.com/' in post.url:
            # The URL is a direct link to the image.
            mo = imgurUrlPattern.search(post.url)
            img_file_name = mo.group(2)
            if '?' in img_file_name:
                img_file_name = img_file_name[:img_file_name.find('?')]
            local_file_name = 'reddit_%s_%s_album_None_imgur_%s' %\
                                (target_sub, post.id, img_file_name)
            downloadImage(post.url, local_file_name)
        else:
            print("Post url not an image")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        # no command line options sent:
        print('Usage:')
        print('  python %s subreddit [minimum score]' % (sys.argv[0]))
        sys.exit()
    elif len(sys.argv) >= 2:
        # the subreddit was sepcified:
        targetSubreddit = sys.argv[1]
        if len(sys.argv) >= 3:
            # the desired minimum score was also specified:
            MIN_SCORE = sys.argv[2]

    # Connect to reddit and download the subreddit front page
    r = praw.Reddit(user_agent='test')
    target_sub = r.get_subreddit(targetSubreddit)
    while COUNT <= 500:
        get_posts(target_sub)
