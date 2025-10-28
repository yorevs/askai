#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch and parse full web page content from SerpApi search results
"""

from serpapi import GoogleSearch
import os, requests
from bs4 import BeautifulSoup


def search_and_crawl(query: str, max_pages: int = 3):
    params = {
        "engine": "google",
        "q": query,
        "num": max_pages,
        "api_key": os.getenv("SERPAPI_KEY"),
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    for item in results.get("organic_results", [])[:max_pages]:
        url = item.get("link")
        title = item.get("title")
        print(f"\n# {title}\nURL: {url}")

        try:
            html = requests.get(url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            text = " ".join(s.strip() for s in soup.stripped_strings)
            print(text[:1000])  # first 1000 chars preview
        except Exception as e:
            print(f"Error fetching {url}: {e}")


if (__name__
    == "__main__"):
    search_and_crawl("What is the next Flamengo match?")
