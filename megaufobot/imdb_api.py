"""Client for the free IMDb API at https://imdbapi.dev/.

This API currently does not require an API key. The wrapper normalizes its
responses into a TMDB-like shape so the existing bot can use it with minimal
changes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests


class IMDbAPI:
    def __init__(self, base_url: str = "https://api.imdbapi.dev", timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, params=params or {}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            print(f"IMDbAPI request error: {exc}")
            return None

    @staticmethod
    def _image_url(image: Any) -> Optional[str]:
        if isinstance(image, dict):
            return image.get("url")
        if isinstance(image, str):
            return image
        return None

    @staticmethod
    def _rating_value(item: Dict[str, Any]) -> float:
        rating = item.get("rating") or {}
        if isinstance(rating, dict):
            return rating.get("aggregateRating") or 0
        return 0

    @staticmethod
    def _title(item: Dict[str, Any]) -> str:
        return item.get("primaryTitle") or item.get("originalTitle") or item.get("title") or "بدون عنوان"

    def _normalize_title(self, item: Dict[str, Any]) -> Dict[str, Any]:
        imdb_type = str(item.get("type") or "").lower()
        media_type = "tv" if "tv" in imdb_type or "series" in imdb_type else "movie"
        title = self._title(item)
        year = item.get("startYear") or item.get("year") or ""
        image_url = self._image_url(item.get("primaryImage") or item.get("image"))
        return {
            "id": item.get("id"),
            "media_type": media_type,
            "title": title,
            "name": title,
            "original_title": item.get("originalTitle") or title,
            "original_name": item.get("originalTitle") or title,
            "release_date": f"{year}-01-01" if year else "",
            "first_air_date": f"{year}-01-01" if year else "",
            "vote_average": self._rating_value(item),
            "poster_path": image_url,
            "overview": item.get("plot") or item.get("description") or "توضیحاتی موجود نیست.",
            "genres": [
                {"name": genre} if isinstance(genre, str) else genre
                for genre in (item.get("genres") or [])
            ],
            "credits": {"cast": [], "crew": []},
            "videos": {"results": []},
            "images": {"backdrops": [], "posters": []},
            "recommendations": {"results": []},
            "number_of_seasons": item.get("numberOfSeasons") or 0,
            "created_by": [],
            "budget": item.get("budget") or 0,
            "revenue": item.get("grossWorldwide") or 0,
            "runtime": item.get("runtimeMinutes") or 0,
            "status": item.get("status") or "",
            "type": item.get("type") or "",
            "networks": [],
            "number_of_episodes": item.get("numberOfEpisodes") or 0,
            "raw": item,
        }

    def search_titles(self, query: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        data = self._get("/search/titles", {"query": query, "limit": limit}) or {}
        titles = data.get("titles") or []
        return {"results": [self._normalize_title(item) for item in titles]}

    def search_multi(self, query: str, page: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        # imdbapi.dev search endpoint only supports query + limit, not page.
        return self.search_titles(query, limit=10)

    def get_title(self, title_id: str) -> Optional[Dict[str, Any]]:
        data = self._get(f"/titles/{title_id}")
        if not data:
            return None
        return self._normalize_title(data)

    def get_movie_details(self, movie_id: str) -> Optional[Dict[str, Any]]:
        return self.get_title(movie_id)

    def get_tv_details(self, tv_id: str) -> Optional[Dict[str, Any]]:
        return self.get_title(tv_id)

    def list_titles(self, **params: Any) -> Dict[str, List[Dict[str, Any]]]:
        data = self._get("/titles", params) or {}
        titles = data.get("titles") or []
        return {"results": [self._normalize_title(item) for item in titles]}

    def get_popular_movies(self, page: int | None = None) -> Dict[str, List[Dict[str, Any]]]:
        return self.list_titles(types=["MOVIE"], sortBy="SORT_BY_POPULARITY", sortOrder="DESC")

    def get_popular_tv(self, page: int | None = None) -> Dict[str, List[Dict[str, Any]]]:
        return self.list_titles(types=["TV_SERIES"], sortBy="SORT_BY_POPULARITY", sortOrder="DESC")

    def get_trending_movies_day(self, page: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        return self.get_popular_movies(page)

    def get_trending_tv_day(self, page: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        return self.get_popular_tv(page)

    def get_trending_movies_week(self, page: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        return self.get_popular_movies(page)

    def get_trending_tv_week(self, page: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        return self.get_popular_tv(page)

    def get_now_playing_movies(self, page: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        return self.list_titles(types=["MOVIE"], sortBy="SORT_BY_RELEASE_DATE", sortOrder="DESC")

    def get_on_the_air_tv(self, page: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        return self.list_titles(types=["TV_SERIES"], sortBy="SORT_BY_RELEASE_DATE", sortOrder="DESC")

    def get_image_url(self, path: Optional[str]) -> Optional[str]:
        return path
