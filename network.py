#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Network layer for Open Calibre Store.

Handles communication with Calibre Content Server OPDS feeds.
"""

import json
import re
import urllib.request
import urllib.parse
import base64


# Used whenever a server has no explicit library id(s) configured,
# which keeps old configs (saved before multi-library support was
# added) working exactly as before.
DEFAULT_LIBRARY_ID = "calibre-library"


# Field prefixes recognized in a raw search query, mapped to the
# field name the Calibre Content Server search grammar expects.
# "keyword(s)"/"tag(s)" all mean the same thing to Calibre: tags.
_FIELD_ALIASES = {
    "title": "title",
    "author": "author",
    "authors": "author",
    "keyword": "tags",
    "keywords": "tags",
    "tag": "tags",
    "tags": "tags",
}

# Matches tokens like `title:foo` or `author:"Jane Doe"` anywhere
# in a query string.
_FIELD_TOKEN_RE = re.compile(
    r'(?P<field>[A-Za-z]+):(?P<value>"[^"]*"|\S+)'
)


def build_search_query(raw_query):

    """
    Turn what the user typed into a Calibre Content Server search
    query, restricting *unqualified* text to the title, author and
    tags fields so it can no longer false-positive match on
    comments/full text.

    - If the user already used field prefixes we understand
      (title:, author:/authors:, keyword(s):/tag(s):), those are
      translated to Calibre's own field names (keywords/tag(s) ->
      tags) and passed through untouched otherwise.
    - If there are no recognized field prefixes at all, the whole
      query is turned into (title:"..." or author:"..." or
      tags:"...") so it only ever matches those three fields.
    """

    # Calibre 9.14 can provide the store search query as bytes.
    # The query parser below uses string regexes, so normalize it to
    # text before doing any regex or string operations.
    if isinstance(raw_query, bytes):
        raw_query = raw_query.decode("utf-8", errors="replace")
    elif raw_query is None:
        raw_query = ""
    else:
        raw_query = str(raw_query)

    raw_query = raw_query.strip()

    if not raw_query:
        return raw_query

    matches = list(
        _FIELD_TOKEN_RE.finditer(raw_query)
    )

    recognized = [
        m for m in matches
        if m.group("field").lower() in _FIELD_ALIASES
    ]

    if recognized:

        parts = []
        cursor = 0

        for m in matches:

            field = m.group("field").lower()
            value = m.group("value")
            start, end = m.span()

            # Preserve any free text that appeared between tokens
            # (e.g. connectors the user typed) as-is.
            between = raw_query[cursor:start].strip()

            if between:
                parts.append(between)

            if field in _FIELD_ALIASES:
                parts.append(
                    f"{_FIELD_ALIASES[field]}:{value}"
                )
            else:
                parts.append(f"{field}:{value}")

            cursor = end

        trailing = raw_query[cursor:].strip()

        if trailing:
            parts.append(trailing)

        return " ".join(parts)

    # No field prefixes given: restrict the free-text query to
    # title/author/tags instead of letting Calibre fall back to a
    # full-text search that also matches comments.
    escaped = raw_query.replace('"', '\\"')

    return (
        f'(title:"{escaped}" '
        f'or author:"{escaped}" '
        f'or tags:"{escaped}")'
    )


class OpenCalibreClient:


    def __init__(self, server):

        self.server = server

        self.host = server.get(
            "host",
            ""
        )

        self.port = server.get(
            "port",
            8080
        )

        self.https = server.get(
            "https",
            False
        )

        self.username = server.get(
            "username"
        )

        self.password = server.get(
            "password"
        )

        #
        # One server can expose multiple libraries, each with its
        # own name (Calibre's default is "calibre-library", but
        # renamed/multi-library setups are common). Older configs
        # saved before this existed won't have a "libraries" key
        # at all, so fall back to the historical default.
        #
        libraries = server.get(
            "libraries"
        )

        if not libraries:
            libraries = [DEFAULT_LIBRARY_ID]

        self.libraries = libraries


    def base_url(self):

        protocol = (
            "https"
            if self.https
            else "http"
        )

        return (
            f"{protocol}://"
            f"{self.host}:"
            f"{self.port}"
        )


    def request(
        self,
        url,
        timeout=30
    ):

        headers = {
            "User-Agent":
                "Calibre OpenCalibre Store"
        }


        if self.username:

            token = base64.b64encode(
                (
                    self.username
                    + ":"
                    + self.password
                ).encode()
            ).decode()


            headers[
                "Authorization"
            ] = (
                "Basic "
                + token
            )


        req = urllib.request.Request(
            url,
            headers=headers
        )


        with urllib.request.urlopen(
            req,
            timeout=timeout
        ) as response:

            return response.read()



    def search(
        self,
        query,
        timeout=30
    ):

        """
        Search every library configured for this server and
        return the combined results.
        """

        refined_query = build_search_query(
            query
        )

        encoded = urllib.parse.quote(
            refined_query
        )

        results = []

        for library_id in self.libraries:

            url = (
                self.base_url()
                +
                "/opds/search/"
                +
                encoded
                +
                "?library_id="
                +
                urllib.parse.quote(
                    library_id
                )
            )

            try:

                print(
                    "Searching:",
                    url
                )


                data = self.request(
                    url,
                    timeout
                )


                print(
                    "Response received:",
                    len(data),
                    "bytes"
                )


                results.extend(
                    self.parse_response(
                        data,
                        library_id
                    )
                )


            except Exception as err:

                #
                # One library failing (wrong name, temporarily
                # unavailable, etc.) shouldn't stop the others
                # on the same server from being searched.
                #
                print(
                    "Search failed for library",
                    library_id,
                    ":",
                    err
                )

        return results



    def parse_response(
        self,
        data,
        library_id=DEFAULT_LIBRARY_ID
    ):

        """
        Parse server response.

        Supports:
        - JSON
        - OPDS XML
        """

        # Try JSON

        try:

            obj = json.loads(
                data.decode(
                    "utf-8"
                )
            )


            return obj.get(
                "books",
                []
            )


        except Exception:

            pass



        # Try OPDS XML

        try:

            from .opds import parse_opds


            return parse_opds(
                data,
                self.base_url(),
                library_id
            )


        except Exception as err:

            print(
                "OPDS parse failed:",
                err
            )


        return []
