# Open Calibre Store Plugin

A Calibre **Get Books** plugin that enables searching and downloading from one or more Open Calibre servers directly within Calibre.

---

## Features

- **Multi-Server Search:** Query multiple Open Calibre servers simultaneously.
- **Flexible Network Support:** Works across LAN libraries via local IP addresses or hostnames over HTTP and HTTPS.
- **Authentication:** Supports basic authentication credentials.
- **OPDS Parsing:** Native OPDS feed parsing for accurate metadata retrieval.
- **Smart Filtering:** Automatic duplicate result filtering.
- **Direct Downloads:** Seamlessly download free books directly through Calibre.

---

## Installation

1. Open **Calibre**.
2. Navigate to **Preferences** > **Plugins** > **Load plugin from file**.
3. Select `OpenCalibreStore.zip`.
4. Restart Calibre to complete installation.

---

## Configuration

1. Go to **Preferences** $\rightarrow$ **Plugins** $\rightarrow$ **Open Calibre Servers**.
2. Click **Customize Plugin**.
3. Add your target server addresses using the following format:

| Field | Example Value |
| :--- | :--- |
| **Host** | `192.168.1.100` |
| **Port** | `8080` |

### Supported Server Formats

You can add multiple servers across local and remote locations:

- `192.168.1.100:8080`
- `10.0.0.50:8080`
- `books.example.com:443`

### Supported Server Paths

The plugin expects an Open Calibre server exposing an OPDS feed. Common paths tested include:

- `/opds/search/`
- `/opds/search?q=`
- `/search?q=`

---

## Folder Structure

```text
OpenCalibreStore/
├── __init__.py
├── store.py
├── config.py
├── network.py
├── opds.py
├── metadata.py
├── plugin-import-name.txt
└── README.md
