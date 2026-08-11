#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Metadata helpers for Open Calibre Store.

Converts Open Calibre/OPDS data into
Calibre-friendly metadata objects.
"""

from calibre.ebooks.metadata.book.base import Metadata


def create_metadata(book):
    """
    Convert a book dictionary into a
    Calibre Metadata object.
    """

    title = book.get(
        "title",
        "Unknown Title"
    )

    author = book.get(
        "author",
        "Unknown"
    )


    mi = Metadata(
        title,
        [author]
    )


    if book.get(
        "cover"
    ):

        mi.cover_url = (
            book["cover"]
        )


    if book.get(
        "formats"
    ):

        mi.formats = (
            book["formats"]
        )


    if book.get(
        "url"
    ):

        mi.identifiers = {

            "opencalibre":
                book["url"]

        }


    return mi



def normalize_book(entry):

    """
    Normalize incoming data from
    different Open Calibre APIs.
    """

    return {

        "title":
            entry.get(
                "title",
                ""
            ),

        "author":
            entry.get(
                "author",
                ""
            ),

        "cover":
            entry.get(
                "cover"
            ),

        "url":
            entry.get(
                "url"
            ),

        "formats":
            entry.get(
                "formats",
                ""
            )

    }
