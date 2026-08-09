#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Network layer for Open Calibre Store.

Handles communication with Calibre Content Server OPDS feeds.
"""

import json
import urllib.request
import urllib.parse
import base64


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
        Search Calibre OPDS server.
        """

        encoded = urllib.parse.quote(
            query
        )


        url = (
            self.base_url()
            +
            "/opds/search/"
            +
            encoded
            +
            "?library_id=calibre-library"
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


            return self.parse_response(
                data
            )


        except Exception as err:

            print(
                "Search failed:",
                err
            )

            return []



    def parse_response(
        self,
        data
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
                self.base_url()
            )


        except Exception as err:

            print(
                "OPDS parse failed:",
                err
            )


        return []