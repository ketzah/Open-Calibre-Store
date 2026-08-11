# Open Calibre Store Plugin

A Calibre "Get Books" plugin that lets you search one or more Open
Calibre servers from inside Calibre.

## Features

- Search multiple Open Calibre servers, each with one or more libraries
- Works with LAN libraries, IP addresses, and hostnames
- HTTP and HTTPS support, with basic authentication
- OPDS feed parsing
- Duplicate result filtering
- Free book downloads through Calibre

---

## Installation

1. Open Calibre.
2. Go to Preferences -> Plugins -> Load plugin from file.
3. Select OpenCalibreStore.zip.
4. Restart Calibre.

---

## Configuration

After installing, go to Preferences -> Plugins -> Open Calibre
Servers -> Customize Plugin, and add your server(s).

For a single server, fill in the host (e.g. 192.168.1.100), the
port (e.g. 8080), and, optionally, one or more library IDs. Each
server can expose one or more libraries under any name you've
given them - not just the default "calibre-library". Leave the
Library ID(s) field blank to use Calibre's default library, or
enter a comma-separated list (e.g. "Fiction, Nonfiction") to search
several libraries on that server.

You can also add several servers at once with Bulk Add, one per
line:

    192.168.1.100:8080
    10.0.0.50:8080
    books.example.com:443

To specify library IDs in Bulk Add, append them after a pipe (|):

    192.168.1.100:8080|Fiction,Nonfiction
    10.0.0.50:8080|MyLibrary

---

## Search syntax

By default, a plain search (with no field prefix) only matches
Title, Author, and Tags. It will not match against comments or
other full-text fields, which keeps false positives down.

To search a specific field, use one of these prefixes:

    title:Foundation
    author:Asimov
    keywords:scifi     (matches Tags)
    tags:scifi

You can combine prefixes in a single search, for example:

    title:Foundation author:Asimov

---

## Supported servers

The plugin expects an Open Calibre server exposing an OPDS feed.
It has been tested against these paths:

    /opds/search/
    /opds/search?q=
    /search?q=

---

## Folder structure

    OpenCalibreStore/
        __init__.py
        store.py
        config.py
        network.py
        opds.py
        metadata.py
        plugin-import-name.txt
        README.md

---

## Troubleshooting

### Server does not appear

Check that:

- The IP address is reachable
- The port is correct
- Your firewall allows access
- The OPDS endpoint is enabled on the server

You can sanity-check this by opening
http://server-ip:port/opds in a browser - if that loads a feed,
Calibre should be able to reach it too.

### Search returns nothing

Turn on debug logging in Calibre (Preferences -> Miscellaneous ->
Debug device detection) and check the debug output for errors from
this plugin.

---

## Development

The plugin's source lives under
calibre_plugins.open_calibre_store, with the work split across a
few files:

- store.py - Calibre "Get Books" integration
- network.py - HTTP communication with the server(s)
- opds.py - OPDS feed parsing
- config.py - server configuration UI and storage

---

## License

MIT License
