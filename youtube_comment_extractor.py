import requests
import re
import json
import time

class Comments:
    def __init__(self, url=None):
        '''
        This class is responsible for:
        1. Creating contiunation url, track_params, session_token
        2. Grabbing JSON details
        3. Processing JSON
        4. Returning Dict of comment, like,  owner, owner thumbnail and owner url

        ** Replies option coming soon

        Usage:

        a = Comments('youtube url').process_comments(count=45[optional])
        print(a)
        '''
        self.request = requests.sessions.Session()
        self.request.headers = {'X-YouTube-Client-Name': '1',
                                'X-YouTube-Client-Version': '2.20201202.06.01',
                                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.55'}
        self.continuation, self.track_params, self.token = self.get_continuation_data(url)
        self.initial_json, self.comment_count, self.page_len, self.page_count = self.get_basic_details(self.continuation, self.track_params, self.token)

    def get_basic_details(self, continuation, track_params, token):
        '''
        Gets the basic details

        Params:
            continuation: str -> continuation token
            track_params:str -> Tracking params for comments
            token:str -> Session token aka xsrf_token

        Returns: list()
            a: dict -> data for first comments page
            count:int -> total number of comments
            page_len:int -> number of comments in each page
            page_count -> number of pages for all comments
        '''
        a = self.request.post(f'https://www.youtube.com/comment_service_ajax?action_get_comments=1&pbj=1&ctoken={continuation}&continuation={continuation}&itct={track_params}', data={'session_token': token}).json()
        
        
        # print(a.json()['response']['continuationContents']['itemSectionContinuation']['contents'])
        # count = re.search(r'"countText":.*?"text":"(.*?) Comments"', a.text).groups()[0].replace(',', '')
        page_len = len(a['response']['continuationContents']['itemSectionContinuation']['contents'])
        # page_len = len(json.loads(a)['response']['continuationContents']['itemSectionContinuation']['contents'])
        # print(page_len)
        count=a['response']['continuationContents']['itemSectionContinuation']['header']['commentsHeaderRenderer']['commentsCount']['runs'][0]['text']
        page_count = int(count)//page_len
        return (a, int(count), page_len, page_count)

    def get_continuation_data(self, url):
        '''
        Params:
            url[optional] : URL of the Youtube video

        Returns:
            Continuation data for the first page of comments

        '''
        html = self.request.get(url).text
        
        a, b = re.search(r'"continuation":"(.*?)","clickTrackingParams":"(.*?)"', html).groups()
        b = b.replace('=', '%3D')
        token = re.search(r'"XSRF_TOKEN":"(.*?)"', html).groups()[0].replace('\\u003d', '=')
        return (a, b, token)

    def search_dict(self, partial, key):
        """
        A handy function that searches for a specific `key` in a `data` dictionary/list
        """
        if isinstance(partial, dict):
            for k, v in partial.items():
                if k == key:
                    # found the key, return the value
                    yield v
                else:
                    # value of the dict may be another dict, so we search there again
                    for o in self.search_dict(v, key):
                        yield o
        elif isinstance(partial, list):
            # if the passed data is a list
            # iterate over it & search for the key at the items in the list
            for i in partial:
                for o in self.search_dict(i, key):
                    yield o


    def find_value(self, html, key, num_sep_chars=2, separator='"'):
        # define the start position by the position of the key + 
        # length of key + separator length (usually : and ")
        start_pos = html.find(key) + len(key) + num_sep_chars
        # the end position is the position of the separator (such as ")
        # starting from the start_pos
        end_pos = html.find(separator, start_pos)
        # return the content in this range
        return html[start_pos:end_pos]

    def process_comments(self, count: int = None, on_progress=None):
        '''
        This function processes the whole comment system.
        count:int -> number of comments you want. All by default
        on_progress:function -> Name of user-defined function for logging. Return page currently processing and total number of pages required

        Returns:list()
        list of Dict of comment, like, owner name, owner thumbnail and owner url
        '''
        continuation = ''
        track_params = ''
        token = ''
        if count is None:
            end_range = self.page_count
            count = self.comment_count
        elif count > self.comment_count:
            raise Exception("Count can't be greater that total comment count")
        else:
            count = count
            end_range = count//self.page_len+1
        comments = []
        for k in range(0, end_range):
            if on_progress is not None:
                on_progress(page_num=k, total_pages=end_range)
            if k == 0:
                json_data = self.initial_json
            else:
                # json_data = self.request.post(f"https://www.youtube.com/comment_service_ajax?action_get_comments=1&pbj=1&ctoken={continuation}&continuation={continuation}&itct={track_params}", data={'session_token': token}).text
                json_data = self.request.post(f"https://www.youtube.com/comment_service_ajax?action_get_comments=1&pbj=1&ctoken={continuation}&continuation={continuation}&itct={track_params}", data={'session_token': token}).json()
            
            print(json_data.keys())
            comment_json = json_data['response']['continuationContents']['itemSectionContinuation']['contents']
            token = json_data['xsrf_token']

            # handling with error
            try:
                continuation = json_data['response']['continuationContents']['itemSectionContinuation']['continuations'][0]["nextContinuationData"]['continuation']
                track_params = json_data['response']['continuationContents']['itemSectionContinuation']['continuations'][0]["nextContinuationData"]["clickTrackingParams"]
            except:
                continuation = ''
                track_params = ''

            for i in comment_json:
                data = i['commentThreadRenderer']
                cd = data['comment']['commentRenderer']
                comment = ''.join([j['text'] for j in cd['contentText']['runs']])
                try:
                    comment_owner = cd['authorText']['simpleText']
                except Exception:
                    comment_owner = 'Undefined'
                comment_owner_thumb = cd['authorThumbnail']['thumbnails'][-1]['url']
                comment_owner_url = cd['authorEndpoint']['browseEndpoint']['canonicalBaseUrl']
                likes = cd['likeCount']
                comments.append({'comment': comment, 'likes': likes, 'owner': comment_owner, 'thumbnail': comment_owner_thumb, 'owner_url': comment_owner_url})
            time.sleep(1)            
        return comments[0:count]
