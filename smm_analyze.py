from instabot import Bot
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from dateutil import relativedelta
from collections import defaultdict
import argparse
import pprint
import requests
from requests import ConnectionError
from requests import HTTPError
from urllib3.exceptions import ResponseError
import json
import time


VK_API = 5.103
VK_BASE_URL = 'https://api.vk.com/method/{0}'
FB_BASE_URL = 'https://graph.facebook.com/'


class VkAPIUnavailable(Exception):
    """Class for handle api.vk.com exceptions."""


class FaceBookAPIUnavailable(Exception):
    """Class for handle graph.facebook.com exceptions."""


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('social_media')
    return parser.parse_args()


def get_last_date(now, months=0, weeks=0):
    if months:
        return now + relativedelta.relativedelta(months=months)
    elif weeks:
        return now + relativedelta.relativedelta(weeks=weeks)


def instabot_init(insta_vendor_name):
    insta_login = getenv('INSTA_LOGIN')
    insta_password = getenv('INSTA_PASSWORD')
    bot = Bot()
    bot.login(username=insta_login, password=insta_password)
    return bot


def get_vk_media_likers(media_id, group_id):
    media_likers = []
    likes_per_page = 1000
    payload = {
        'type': 'post',
        'owner_id': group_id,
        'item_id': media_id,
        'friends_only': 0,
        'count': likes_per_page,
    }
    url = VK_BASE_URL.format('likes.getList')
    json_data, response_text = invoke_vk_api(url, payload)
    likes_count = unpack_vk_response(
        unpack_method='count',
        json_data=json_data,
        dest_url=url,
        response_text=response_text,
        )
    offset = 0
    while offset < likes_count:
        payload['offset'] = offset
        json_data, response_text = invoke_vk_api(url, payload)
        media_likers_data = unpack_vk_response(
            unpack_method='items',
            json_data=json_data,
            dest_url=url,
            response_text=response_text,
            )
        media_likers.extend(media_likers_data)
        offset += likes_per_page
    return media_likers


def filter_vk_comments_by_date(now, comments_list):
    return [
        comment for comment in comments_list
        if get_last_date(now, weeks=-2) <=
        datetime.fromtimestamp(comment['date'])
        <= now
        ]


def get_vk_commenters(comments_list, group_id):
    return list(
        {comment['from_id'] for comment in comments_list
         if 'from_id' in comment
         and comment['from_id'] != group_id
         })


def invoke_vk_api(url, payload):
    access_token = getenv('VK_ACCESS_TOKEN')
    payload['access_token'] = access_token
    payload['v'] = VK_API
    try:
        response = requests.get(url, params=payload)
    except (ConnectionError, ResponseError):
        raise VkAPIUnavailable('{0} is not available!'.format(url))
    try:
        response.raise_for_status()
    except HTTPError:
        raise VkAPIUnavailable(response.text)
    return response.json(), response.text


def get_vk_media_comments(media_id, group_id):
    media_comments = []
    comments_per_page = 100
    offset = 0
    payload = {
        'owner_id': group_id,
        'post_id': media_id,
        'count': comments_per_page,
    }
    url = VK_BASE_URL.format('wall.getComments')
    json_data, response_text = invoke_vk_api(url, payload)
    comments_count = unpack_vk_response(
        unpack_method='count',
        json_data=json_data,
        dest_url=url,
        response_text=response_text,
    )
    while offset < comments_count:
        payload['offset'] = offset
        json_data, response_text = invoke_vk_api(url, payload)
        media_comments_data = unpack_vk_response(
            unpack_method='items',
            json_data=json_data,
            dest_url=url,
            response_text=response_text,
        )
        media_comments.extend(media_comments_data)
        offset += comments_per_page
    return media_comments


def get_vk_medias(vk_vendor_name):
    vk_medias = []
    wall_records_count = 100
    payload = {
        'domain': vk_vendor_name,
        'count': wall_records_count,
    }
    url = VK_BASE_URL.format('wall.get')
    json_data, response_text = invoke_vk_api(url, payload)
    medias_count = unpack_vk_response(
        unpack_method='count',
        json_data=json_data,
        dest_url=url,
        response_text=response_text,
    )
    offset = 0
    while offset < medias_count:
        payload['offset'] = offset
        json_data, response_text = invoke_vk_api(url, payload)
        vk_medias_data = unpack_vk_response(
            unpack_method='items',
            json_data=json_data,
            dest_url=url,
            response_text=response_text,
        )
        vk_medias.extend(vk_medias_data)
        offset += wall_records_count
    return vk_medias


def dt_from_utc_to_local(utc_datetime_str):
    utc_datetime = datetime.strptime(
        utc_datetime_str,
        '%Y-%m-%dT%H:%M:%S%z',
        )
    now_timestamp = time.time()
    offset = (
        datetime.fromtimestamp(now_timestamp) -
        datetime.utcfromtimestamp(now_timestamp)
        )
    return utc_datetime.replace(tzinfo=None) + offset


def get_facebook_commenters(comments_data, now, last_date):
    commenters = set()
    for comments in comments_data:
        for comment in comments['data']:
            comment_date = dt_from_utc_to_local(comment['created_time'])
            if last_date <= comment_date <= now:
                commenters.add(comment['from']['id'])
    return list(commenters)


def get_facebook_media_comments(media_id):
    facebook_access_token = getenv('FACEBOOK_TOKEN')
    dest_url = '{0}/{1}/comments'.format(FB_BASE_URL, media_id)
    payload = {
        'access_token': facebook_access_token,
     }
    try:
        response = requests.get(dest_url, params=payload)
    except (ConnectionError, ResponseError):
        raise FaceBookAPIUnavailable('{0} is not available!'.format(dest_url))
    try:
        response.raise_for_status()
    except HTTPError:
        raise FaceBookAPIUnavailable(response.text)
    return response.json()


def get_facebook_reactions(media_id):
    facebook_access_token = getenv('FACEBOOK_TOKEN')
    dest_url = '{0}/{1}/reactions'.format(FB_BASE_URL, media_id)
    payload = {
        'access_token': facebook_access_token,
     }
    try:
        response = requests.get(dest_url, params=payload)
    except (ConnectionError, ResponseError):
        raise FaceBookAPIUnavailable('{0} is not available!'.format(dest_url))
    try:
        response.raise_for_status()
    except HTTPError:
        raise FaceBookAPIUnavailable(response.text)
    return response.json()


def get_facebook_medias(facebook_access_token, group_id):
    dest_url = '{0}/{1}/'.format(FB_BASE_URL, group_id)
    payload = {
        'access_token': facebook_access_token,
        'fields': 'feed',
     }
    try:
        response = requests.get(dest_url, params=payload)
    except (ConnectionError, ResponseError):
        raise FaceBookAPIUnavailable('{0} is not available!'.format(dest_url))
    try:
        response.raise_for_status()
    except HTTPError:
        raise FaceBookAPIUnavailable(response.text)
    json_data = response.json()
    return [media['id'] for media in json_data['feed']['data']]


def build_facebook_statistics(commenters, reactions_data):
    facebook_statistics = {}
    user_reactions_statistics = defaultdict(int)
    for commenter in set(commenters):
        for reactions in reactions_data:
            for reaction in reactions['data']:
                user_reactions_statistics[reaction['type']] += 1
        facebook_statistics[commenter] = dict(user_reactions_statistics)
    return facebook_statistics


def get_facebook_analyze(*args):
    now = datetime.now()
    last_date = get_last_date(now, months=-1)
    facebook_access_token = getenv('FACEBOOK_TOKEN')
    group_id = getenv('FACEBOOK_GROUP')
    medias = get_facebook_medias(facebook_access_token, group_id)
    commenters = []
    comments = []
    reactions = []
    for media in medias:
        media_comments = get_facebook_media_comments(media)
        comments.append(media_comments)
        media_commenters = get_facebook_commenters(comments, now, last_date)
        commenters.extend(media_commenters)
        media_reactions = get_facebook_reactions(media)
        reactions.append(media_reactions)
    return build_facebook_statistics(commenters, reactions)


def get_instagram_analyze(*args):
    now = datetime.now()
    insta_vendor_name, = args
    last_date = get_last_date(now, months=-3)
    bot = instabot_init(insta_vendor_name)
    user_id = bot.get_user_id_from_username(insta_vendor_name)
    media_slice = slice(0, 5)
    user_medias = bot.get_total_user_medias(user_id)[media_slice]
    comments_top = defaultdict(int)
    posts_top = defaultdict(int)
    instagram_statistics = {}
    for media in user_medias:
        media_info,  = bot.get_media_info(media)
        media_dt = datetime.fromtimestamp(media_info['caption']['created_at'])
        is_valid_date = last_date <= media_dt <= now
        if not is_valid_date:
            continue
        media_comments = bot.get_media_comments_all(media)
        commenters = [comment['user_id'] for comment in media_comments]
        unique_commenters = set(commenters)
        for commenter in commenters:
            comments_top[commenter] += 1
        for unique_commenter in unique_commenters:
            posts_top[unique_commenter] += 1
    instagram_statistics['Comments Top'] = dict(comments_top)
    instagram_statistics['Posts Top'] = dict(posts_top)
    return instagram_statistics


def unpack_vk_response(
    unpack_method=None,
    json_data=None,
    dest_url=None,
    response_text=None,
):
    unpack_methods = {
        'count': 'count',
        'items': 'items',
    }
    try:
        if unpack_method == 'id':
            return json_data['response'][0]['id']
        return json_data['response'][unpack_methods[unpack_method]]
    except KeyError:
        response_error = json.loads(response_text)
        error_code = response_error['error']['error_code']
        error_msg = response_error['error']['error_msg']
        raise VkAPIUnavailable(
            """\t\tSomething went wrong during getting vk group-id!\n
                API-method - {0}\n
                error_code - {1}\n
                error_msg - {2}""".format(dest_url, error_code, error_msg),
                )


def get_vk_group_id(vendor_name):
    payload = {
        'group_ids': vk_vendor_name,
    }
    url = '{0}/{1}'.format(VK_BASE_URL, 'groups.getById')
    json_data, response_text = invoke_vk_api(url, payload)
    vk_group_id = unpack_vk_response(
        unpack_method='id',
        json_data=json_data,
        dest_url=url,
        response_text=response_text,
    )
    return -vk_group_id


def get_vk_analyze(vk_vendor_name):
    vk_group_id = get_vk_group_id(vk_vendor_name)
    vk_medias = get_vk_medias(vk_vendor_name)
    audience_core = set()
    for media in vk_medias:
        vk_media_comments = get_vk_media_comments(media['id'], vk_group_id)
        last_two_week_comments = filter_vk_comments_by_date(
            datetime.now(),
            vk_media_comments,
            )
        vk_commenters = get_vk_commenters(last_two_week_comments, vk_group_id)
        vk_media_likers = get_vk_media_likers(media['id'], vk_group_id)
        intersect = list(set(vk_commenters) & set(vk_media_likers))
        audience_core.update(intersect)
    return audience_core


if __name__ == '__main__':
    load_dotenv()
    pp = pprint.PrettyPrinter(indent=4)
    cli_args = arg_parser()
    social_media = cli_args.social_media
    vk_vendor_name = getenv('VK_VENDOR')
    insta_vendor_name = getenv('INSTA_VENDOR')
    analyze_methods = {
        'instagram': (get_instagram_analyze, insta_vendor_name),
        'vk': (get_vk_analyze, vk_vendor_name),
        'facebook': (get_facebook_analyze),
    }
    analyze_method, vendor_name = analyze_methods[social_media]
    try:
        analyze_result = analyze_method(vendor_name)
    except VkAPIUnavailable as vk_error:
        pp.pprint('\t\tError during getting VK-analyze:\n{0}'.format(vk_error))
    except FaceBookAPIUnavailable as fb_error:
        pp.pprint('Error during getting FB-analyze:\n{0}'.format(fb_error))
    pp.pprint(analyze_result)
