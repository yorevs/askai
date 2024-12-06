#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: demo.components
      @file: summarizer-demo.py
   @created: Tue, 14 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.component.cache_service import cache
from askai.core.component.summarizer import summarizer
from askai.core.support.langchain_support import lc_llm
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.tools.commons import sysout
from langchain_community.document_loaders.directory import DirectoryLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from utils import init_context

import os

if __name__ == "__main__":
    init_context("summarizer-demo")
    sysout("-=" * 40)
    sysout("AskAI Summarizer Demo")
    sysout("-=" * 40)
    folder, glob = os.getenv("HOME") + "/HomeSetup", "**/*.md"
    sysout(f"%GREEN%Summarizing: {folder}/{glob} ...")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    documents: List[Document] = DirectoryLoader(
        "~/HomeSetup/docs", glob="**/*.md"
    ).load()
    embeddings = lc_llm.create_embeddings.embed_documents(documents)

    sysout(f"READY to answer")
    sysout("--" * 40)
    while (query := line_input("You: ")) not in ["exit", "q", "quit"]:
        results: List[str] = [f"%GREEN%AI: {r.answer}" for r in summarizer.query(query)]
        list(map(sysout, results))
    cache.save_input_history()
