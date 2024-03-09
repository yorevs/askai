import os
from dataclasses import dataclass
from typing import List


@dataclass
class InternetResearch:
    """Keep track of the internet search responses."""

    keywords: List[str]
    urls: List[str]
    results: List[str]


if __name__ == '__main__':
    from langchain_community.utilities import GoogleSearchAPIWrapper
    from langchain_core.tools import Tool

    search = GoogleSearchAPIWrapper()

    tool = Tool(
        name="google_search",
        description="Search Google for recent results.",
        func=search.run,
    )

    print(tool.run("Obama's first name?"))
    # from googleapiclient.discovery import build
    # import pprint
    #
    # my_api_key = os.environ.get("GOOGLE_API_KEY")
    # my_cse_id = os.environ.get("GOOGLE_CSE_ID")
    #
    # def google_search(search_term, api_key, cse_id, **kwargs):
    #     service = build("customsearch", "v1", developerKey=api_key)
    #     res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    #     return res['items']
    #
    # results = google_search(
    #     'stackoverflow site:en.wikipedia.org', my_api_key, my_cse_id, num=10)
    # for result in results:
    #     pprint.pprint(result)
