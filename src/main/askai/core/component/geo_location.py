#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: geo_location.py
   @created: Tue, 23 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from askai.core.askai_configs import configs
from datetime import datetime
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.namespace import Namespace
from hspylib.modules.fetch import fetch
from json import JSONDecodeError
from requests.exceptions import ConnectionError
from textwrap import dedent

import json
import logging as log
import pytz


class GeoLocation(metaclass=Singleton):
    """TODO"""

    INSTANCE: "GeoLocation"

    GEO_LOC_URL: str = "http://ip-api.com/json"

    EMPTY_JSON_RESP: str = dedent(
        """
    {
        "status": "failure", "country": "", "countryCode": "", "region": "", "regionName": "",
        "city": "", "zip": "", "lat": 0.0, "lon": 0.0, "timezone": "",
        "isp": "", "org": "", "as": "", "query": ""
    }
    """
    )

    # Date format used in prompts, e.g: Fri 22 Mar 19:47 2024.
    DATE_FMT: str = "%a %d %b %-H:%M %Y"

    @classmethod
    def get_location(cls, ip: str = None) -> Namespace:
        """TODO"""
        try:
            url = f"{cls.GEO_LOC_URL}{'/' + ip if ip else ''}"
            log.debug("Fetching the Geo Position from: %s", url)
            geo_req = fetch.get(url)
        except (JSONDecodeError, ConnectionError) as err:
            log.error("Failed to retrieve geo location => %s", str(err))
            geo_req = Namespace(body=cls.EMPTY_JSON_RESP)
        geo_json = json.loads(geo_req.body)
        geo_location: Namespace = Namespace(**geo_json)
        return geo_location

    def __init__(self, ip: str = None):
        self._geo_location = self.get_location(ip)
        self._idiom: str = configs.language.idiom

    def __str__(self):
        geo_loc = self._geo_location
        geo_loc.setattr("zoned_datetime", self.datetime)
        return str(self._geo_location)

    @property
    def latitude(self) -> float:
        return self._geo_location.lat

    @property
    def longitude(self) -> float:
        return self._geo_location.lon

    @property
    def country(self) -> str:
        return self._geo_location.country

    @property
    def country_code(self) -> str:
        return self._geo_location.countryCode

    @property
    def region(self) -> str:
        return self._geo_location.region

    @property
    def region_name(self) -> str:
        return self._geo_location.regionName

    @property
    def city(self) -> float:
        return self._geo_location.city

    @property
    def zip(self) -> str:
        return self._geo_location.zip

    @property
    def timezone(self) -> str:
        return self._geo_location.timezone

    @property
    def location(self) -> str:
        return f"{self.city}, {self.region_name} {self.country}"

    @property
    def datetime(self) -> str:
        utc_datetime = datetime.utcnow().replace(tzinfo=pytz.utc)
        zoned_datetime = utc_datetime.astimezone(pytz.timezone(self.timezone))
        return zoned_datetime.strftime(self.DATE_FMT)


assert (geo_location := GeoLocation().INSTANCE) is not None
