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
import os
from json import JSONDecodeError
from textwrap import dedent
import json
import logging as log

from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.namespace import Namespace
from hspylib.modules.fetch import fetch
from requests.exceptions import ConnectionError, ReadTimeout
import pytz

from askai.core.askai_configs import configs
from askai.core.component.cache_service import GEO_LOC_CACHE_FILE


class GeoLocation(metaclass=Singleton):
    """A class for managing and retrieving geographic location data."""

    INSTANCE: "GeoLocation"

    GEO_LOC_URL: str = "http://ip-api.com/json"

    # fmt: off
    DEFAULT_GEO_LOC: str = dedent("""\
        {
            "status": "failure", "isp": "N/A", "org": "N/A", "as": "N/A", "query": "N/A",
            "country": "United Kingdom", "countryCode": "GB", "region": "GL", "regionName": "Greater London",
            "city": "Greenwich", "zip": "SE10 0AB", "lat": 51.4874, "lon": 0.0045, "timezone": "UTC",
        }
        """).strip()
    # fmt: on

    # Date format used in prompts, e.g: Fri 22 Mar 19:47 2024.
    DATE_FMT: str = "%a %d %b %-H:%M %Y"

    @classmethod
    def get_location(cls, ip: str = None) -> Namespace:
        """Retrieve the geographic location based on the provided IP address.
        :param ip: The IP address to locate. If None, the current device's IP address will be used.
        :return: A Namespace object containing the geolocation data, such as latitude, longitude, city, and country.
        """
        geo_req = Namespace(body=cls.DEFAULT_GEO_LOC)

        try:
            if file_is_not_empty(str(GEO_LOC_CACHE_FILE)):
                geo_req = Namespace(body=GEO_LOC_CACHE_FILE.read_text(Charset.UTF_8.val))
            elif configs.ip_api_enabled:
                url = f"{cls.GEO_LOC_URL}{'/' + ip if ip else ''}"
                log.debug("Fetching the Geo Position from: %s", url)
                geo_req = Namespace(body=fetch.get(url).body)
                with open(str(GEO_LOC_CACHE_FILE), "w") as f_geo_loc:
                    f_geo_loc.write(geo_req.body + os.linesep)
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
