#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OPDS parser for Calibre Content Server.
"""

import xml.etree.ElementTree as ET
import re


ATOM = "{http://www.w3.org/2005/Atom}"


def parse_opds(data, base_url="", library_id="calibre-library"):

    books = []

    root = ET.fromstring(data)


    for entry in root.findall(
        ATOM + "entry"
    ):

        title = ""
        author = ""
        cover = None
        download = None
        detail_url = ""
        formats = []
        downloads_by_format = {}

        MEDIA_TYPE_LABELS = {
            "application/epub+zip": "EPUB",
            "application/x-mobipocket-ebook": "MOBI",
            "application/vnd.amazon.ebook": "AZW",
            "application/vnd.amazon.mobi8-ebook": "AZW3",
            "application/pdf": "PDF",
            "text/plain": "TXT",
        }


        title_node = entry.find(
            ATOM + "title"
        )

        if title_node is not None:

            title = (
                title_node.text
                or ""
            )


        author_node = entry.find(
            ATOM + "author/" + ATOM + "name"
        )

        if author_node is not None:

            author = (
                author_node.text
                or ""
            )


        for link in entry.findall(
            ATOM + "link"
        ):

            href = link.attrib.get(
                "href",
                ""
            )

            rel = link.attrib.get(
                "rel",
                ""
            )

            media = link.attrib.get(
                "type",
                ""
            )


            absolute_href = href


            if href.startswith("/"):

                absolute_href = (
                    base_url
                    +
                    href
                )


            #
            # Acquisition/download link
            #

            if (
                "acquisition"
                in rel
            ):

                #
                # Fallback single URL, kept for
                # backward compatibility with
                # JSON responses that only ever
                # send one "url" field.
                #
                download = absolute_href


                if media:

                    formats.append(
                        media
                    )

                    label = MEDIA_TYPE_LABELS.get(
                        media,
                        media.split("/")[-1].upper()
                    )

                    #
                    # Don't clobber an existing
                    # link for the same format;
                    # first one wins.
                    #
                    if label not in downloads_by_format:

                        downloads_by_format[
                            label
                        ] = absolute_href


                #
                # Build Calibre Content Server
                # book details URL
                #

                match = re.search(
                    r"/get/[^/]+/(\d+)/",
                    href
                )


                if match:

                    book_id = (
                        match.group(1)
                    )


                    detail_url = (
                        base_url
                        +
                        "/#book_id="
                        +
                        book_id
                        +
                        "&library_id="
                        +
                        library_id
                        +
                        "&panel=book_details"
                    )


            #
            # Cover image
            #

            if (
                "cover"
                in rel
                or
                "image"
                in rel
            ):

                cover = absolute_href



        books.append(
            {
                "title": title,

                "author": author,

                "cover": cover,

                "url": download,

                "detail_url": detail_url,

                "formats": ", ".join(formats),

                "downloads": downloads_by_format
            }
        )


    return books
