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

    name = "Open Calibre Servers"

    description = (
        "Search your configured Open Calibre servers "
        "from Calibre Get Books."
    )

    author = "ketzah"

    version = (1, 2, 3)

    drm_free_only = True


    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs
        )

        self.config = get_config()



    def _log_error(self, message):

        """
        calibre only attaches a working `self.log` to store plugins
        in some code paths (e.g. it's missing when search() runs on
        the background download thread), so fall back to plain
        stdout instead of crashing when it isn't there.
        """

        log = getattr(self, "log", None)

        if log is not None:

            try:
                log.error(message)
                return
            except Exception:
                pass

        print(message)



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

                self._log_error(
                    "Open Calibre search failed: {}".format(
                        err
                    )
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
        parent=None,
        detail_item=None,
        external=False
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
