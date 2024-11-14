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
import datetime

from askai.core.askai_configs import configs
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.namespace import Namespace
from hspylib.modules.fetch import fetch
from json import JSONDecodeError
from requests.exceptions import ConnectionError, ReadTimeout
from textwrap import dedent

import json
import logging as log
import pytz


class GeoLocation(metaclass=Singleton):
    """A class for managing and retrieving geographic location data."""

    INSTANCE: "GeoLocation"

    GEO_LOC_URL: str = "http://ip-api.com/json"

    EMPTY_JSON_RESP: str = dedent(
        """
    {
        "status": "failure", "country": "London", "countryCode": "UK", "region": "Greater London",
        "regionName": "England", "city": "Greenwich", "zip": "", "lat": 51.4826, "lon": 0.0077,
        "timezone": "UTC", "isp": "", "org": "", "as": "", "query": ""
    }
    """
    ).strip()

    # Date format used in prompts, e.g: Fri 22 Mar 19:47 2024.
    DATE_FMT: str = "%a %d %b %-H:%M %Y"

    @classmethod
    def get_location(cls, ip: str = None) -> Namespace:
        """Retrieve the geographic location based on the provided IP address.
        :param ip: The IP address to locate. If None, the current device's IP address will be used.
        :return: A Namespace object containing the geolocation data, such as latitude, longitude, city, and country.
        """
        geo_req = Namespace(body=cls.EMPTY_JSON_RESP)

        try:
            if configs.ip_api_enabled:
                url = f"{cls.GEO_LOC_URL}{'/' + ip if ip else ''}"
                log.debug("Fetching the Geo Position from: %s", url)
                geo_req = Namespace(body=fetch.get(url).body)
        except (JSONDecodeError, ConnectionError, ReadTimeout) as err:
            log.error("Failed to retrieve geo location => %s", str(err))

        return Namespace(**(json.loads(geo_req.body)))

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
        return f"%CYAN%{self.city}, {self.region_name}, {self.country}%NC%"

    @property
    def datetime(self) -> str:
        utc_datetime = datetime.datetime.now(datetime.UTC).replace(tzinfo=pytz.utc)
        zoned_datetime = utc_datetime.astimezone(pytz.timezone(self.timezone))
        return zoned_datetime.strftime(self.DATE_FMT)


assert (geo_location := GeoLocation().INSTANCE) is not None
