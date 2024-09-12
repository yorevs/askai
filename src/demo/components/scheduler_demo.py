#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: demo.components
      @file: scheduler-demo.py
   @created: Tue, 14 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import logging as log

from askai.core.component.scheduler import scheduler
from hspylib.core.zoned_datetime import now, SIMPLE_DATETIME_FORMAT

from utils import init_context


def echo(msg: str):
    log.info(f"{msg} {now('[%H:%M:%S]')}")


@scheduler.every(2000, 2000)
def every_2_seconds():
    echo("EVERY-2")


@scheduler.every(4000, 2000)
def every_4_seconds():
    echo("EVERY-4")


@scheduler.every(8000, 2000)
def every_8_seconds():
    echo("EVERY-8")


# @scheduler.at(16, 26, 0)
# def at_1():
#     echo("AT-1")
#
#
# @scheduler.at(16, 26, 10)
# def at_2():
#     echo("AT-2")
#
#
# @scheduler.at(16, 26, 20)
# def at_3():
#     echo("AT-3")


@scheduler.after(second=20)
def after_20_seconds():
    echo("AFTER-20s")


if __name__ == "__main__":
    init_context("scheduler-demo", rich_logging=True, console_enable=True, log_level=log.INFO)
    echo("-=" * 40)
    echo(f"AskAI Scheduler Demo - {scheduler.now.strftime(SIMPLE_DATETIME_FORMAT)}")
    echo("-=" * 40)
    scheduler.start()
    scheduler.join()
