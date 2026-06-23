import requests
from .config import TMDB_API_KEY

class TMDbAPI:
    def __init__(self, api_key=TMDB_API_KEY, language='fa-IR'):
        self.api_key = api_key
        self.language = language
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
    
    def _make_request(self, endpoint, params=None):
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        params['language'] = self.language
        
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None
    
    def search_movie(self, query, page=1):
        endpoint = "/search/movie"
        params = {
            'query': query,
            'page': page,
            'include_adult': 'false'
        }
        return self._make_request(endpoint, params)
    
    def search_tv(self, query, page=1):
        endpoint = "/search/tv"
        params = {
            'query': query,
            'page': page,
            'include_adult': 'false'
        }
        return self._make_request(endpoint, params)
    
    def search_multi(self, query, page=1):
        endpoint = "/search/multi"
        params = {
            'query': query,
            'page': page,
            'include_adult': 'false'
        }
        return self._make_request(endpoint, params)
    
    def get_movie_details(self, movie_id):
        endpoint = f"/movie/{movie_id}"
        params = {
            'append_to_response': 'credits,videos,images,recommendations'
        }
        return self._make_request(endpoint, params)
    
    def get_tv_details(self, tv_id):
        endpoint = f"/tv/{tv_id}"
        params = {
            'append_to_response': 'credits,videos,images,recommendations'
        }
        return self._make_request(endpoint, params)
    
    def get_person_details(self, person_id):
        endpoint = f"/person/{person_id}"
        params = {
            'append_to_response': 'movie_credits,tv_credits,images'
        }
        return self._make_request(endpoint, params)
    
    def get_popular_movies(self, page=None):
        import random
        if page is None:
            page = random.randint(1, 5)
        endpoint = "/movie/popular"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_popular_tv(self, page=None):
        import random
        if page is None:
            page = random.randint(1, 5)
        endpoint = "/tv/popular"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_top_rated_movies(self, page=1):
        endpoint = "/movie/top_rated"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_top_rated_tv(self, page=1):
        endpoint = "/tv/top_rated"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_movie_reviews(self, movie_id, page=1):
        endpoint = f"/movie/{movie_id}/reviews"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_tv_reviews(self, tv_id, page=1):
        endpoint = f"/tv/{tv_id}/reviews"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def discover_movies(self, params):
        endpoint = "/discover/movie"
        return self._make_request(endpoint, params)
    
    def discover_tv(self, params):
        endpoint = "/discover/tv"
        return self._make_request(endpoint, params)
    
    def get_movie_recommendations(self, movie_id, page=None):
        endpoint = f"/movie/{movie_id}/recommendations"
        if page is None:
            import random
            page = random.randint(1, 3)  # انتخاب تصادفی از صفحات 1 تا 3
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_tv_recommendations(self, tv_id, page=None):
        endpoint = f"/tv/{tv_id}/recommendations"
        if page is None:
            import random
            page = random.randint(1, 3)  # انتخاب تصادفی از صفحات 1 تا 3
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_genres(self, media_type='movie'):
        endpoint = f"/genre/{media_type}/list"
        return self._make_request(endpoint)
    
    def get_image_url(self, path):
        if not path:
            return None
        return f"{self.image_base_url}{path}"
    
    def get_trending_movies_day(self, page=1):
        endpoint = "/trending/movie/day"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_trending_tv_day(self, page=1):
        endpoint = "/trending/tv/day"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_trending_movies_week(self, page=1):
        endpoint = "/trending/movie/week"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_trending_tv_week(self, page=1):
        endpoint = "/trending/tv/week"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_now_playing_movies(self, page=1):
        endpoint = "/movie/now_playing"
        params = {'page': page}
        return self._make_request(endpoint, params)
    
    def get_on_the_air_tv(self, page=1):
        endpoint = "/tv/on_the_air"
        params = {'page': page}
        return self._make_request(endpoint, params)
