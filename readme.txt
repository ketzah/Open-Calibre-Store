# Open Calibre Store Plugin

A Calibre Get Books plugin that allows you to search one or more
Open Calibre servers from inside Calibre.

## Features

- Search multiple Open Calibre servers
- Works with LAN libraries
- Supports IP addresses and hostnames
- HTTP and HTTPS support
- Basic authentication support
- OPDS feed parsing
- Duplicate result filtering
- Free book downloads through Calibre
- Bulk server add/test to customize.
- Retest existing servers in the list and remove inaccessible ones

---

# Installation

1. Open Calibre

2. Go to:
Preferences
-> Plugins
-> Load plugin from file


3. Select:


OpenCalibreStore.zip


4. Restart Calibre.

---

# Configuration

After installation:


Preferences
-> Plugins
-> Open Calibre Servers
-> Customize Plugin


Add your servers.

Example:


Name:
Home Library

Host:
192.168.1.100

Port:
8080


Multiple servers can be added.

Example:


192.168.1.100:8080
10.0.0.50:8080
books.example.com:443


---

# Supported Servers

The plugin expects an Open Calibre server exposing an OPDS feed.

Common paths tested:


/opds/search/
/opds/search?q=
/search?q=


---

# Folder Structure


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

# Troubleshooting

## Server does not appear

Verify:

- IP address is reachable
- Port is correct
- Firewall allows access
- OPDS endpoint is enabled

Try opening:


http://server-ip:port/opds


in a browser.

---

## Search returns nothing

Enable logging in Calibre:


Preferences
-> Miscellaneous
-> Debug device detection


Check the debug output.

---

# Development

Source:


calibre_plugins.open_calibre_store


Main components:


store.py


Calibre Get Books integration


network.py


HTTP communication


opds.py


OPDS parsing


config.py


Server configuration

---

# License

MIT License
