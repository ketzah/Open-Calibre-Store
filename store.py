#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Open Calibre Store Plugin

Searches one or more Calibre Content Server OPDS libraries.
"""

from calibre.gui2.store import StorePlugin
from calibre.gui2.store.search_result import SearchResult

from .config import get_config
from .network import OpenCalibreClient


class OpenCalibreStore(StorePlugin):

    name = "Open Calibre Store"

    description = (
        "Search and download books from "
        "your Open Calibre Content Servers "
        "through Calibre Get Books."
    )

    author = "jadex"

    version = (1, 2, 0)

    drm_free_only = True


    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs
        )

        self.config = get_config()



    def search(
        self,
        query,
        max_results=50,
        timeout=30
    ):

        """
        Search all configured servers.
        """

        servers = self.config.get(
            "servers",
            []
        )


        if not servers:
            return


        seen = set()


        for server in servers:

            if not server.get(
                "enabled",
                True
            ):
                continue


            client = OpenCalibreClient(
                server
            )


            try:

                results = client.search(
                    query,
                    timeout
                )


                for book in results:


                    key = (
                        book.get(
                            "title",
                            ""
                        ),
                        book.get(
                            "author",
                            ""
                        )
                    )


                    if key in seen:
                        continue


                    seen.add(key)


                    result = SearchResult()


                    result.title = book.get(
                        "title",
                        "Unknown Title"
                    )


                    result.author = book.get(
                        "author",
                        "Unknown"
                    )


                    result.cover_url = book.get(
                        "cover"
                    )


                    #
                    # This is the "Show in Store" URL
                    #
                    result.detail_item = book.get(
                        "detail_url"
                    )


                    #
                    # Download options
                    #
                    result.downloads = {}

                    by_format = book.get(
                        "downloads"
                    )

                    if by_format:

                        #
                        # Correctly labeled per
                        # actual format, e.g. MOBI
                        # books stay labeled MOBI
                        # instead of being assumed
                        # to be EPUB.
                        #
                        result.downloads.update(
                            by_format
                        )

                    elif book.get(
                        "url"
                    ):

                        #
                        # Fallback for JSON responses
                        # that only send a single url
                        # with no format info. Assumes
                        # EPUB since we have no way to
                        # tell otherwise.
                        #
                        result.downloads[
                            "EPUB"
                        ] = book.get(
                            "url"
                        )


                    result.formats = book.get(
                        "formats",
                        ""
                    )


                    result.price = "Free"

                    result.drm = False


                    yield result



            except Exception as err:

                self.log.error(
                    "Open Calibre search failed: %s",
                    err
                )



    def get_details(
        self,
        id,
        timeout=30
    ):

        """
        Not currently used.
        """

        return None



    def open(
        self,
        parent,
        detail_item,
        *args
    ):

        """
        Open the book detail page when
        the user selects 'Show in Store'.
        """

        if not detail_item:
            return


        from qt.core import (
            QDesktopServices,
            QUrl
        )

        print("Opening store URL:", detail_item)
        
        QDesktopServices.openUrl(
            QUrl(
                detail_item
            )
        )