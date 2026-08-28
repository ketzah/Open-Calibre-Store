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

    version = (1, 2, 4)

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

                # StorePlugin does not provide a .log attribute in
                # all Calibre 9.x versions.  Do not let error
                # reporting itself abort the search worker.
                print(
                    "Open Calibre search failed:",
                    repr(err)
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
        gui=None,
        parent=None,
        detail_item=None,
        external=False
    ):

        """
        Open the store or a specific book detail page.

        Calibre 9.14 expects StorePlugin.open() to receive the
        GUI object as its first argument.  For an individual search
        result, use Calibre's WebStoreDialog so the detail URL is
        opened inside the Get Books store when external browsing is
        not requested.
        """

        if not detail_item:
            return

        from qt.core import QUrl
        from calibre.gui2 import open_url
        from calibre.gui2.store.web_store_dialog import WebStoreDialog

        # Open in the system browser when requested by Calibre or by
        # the plugin's configuration.
        if external or self.config.get("open_external", False):
            open_url(QUrl(detail_item))
            return

        # The detail URL for an Open Calibre server is a fragment URL
        # such as:
        #   http://host:port/#book_id=123&library_id=...&panel=book_details
        # WebStoreDialog needs the server URL as its base URL and the
        # complete detail URL as the target.
        base_url = detail_item.split("#", 1)[0]

        if not base_url:
            base_url = detail_item

        print("Opening store URL:", detail_item)

        d = WebStoreDialog(
            self.gui,
            base_url,
            parent,
            detail_item
        )
        d.setWindowTitle(self.name)
        d.set_tags(self.config.get("tags", ""))
        d.exec()
