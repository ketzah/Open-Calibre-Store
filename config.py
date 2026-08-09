#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration UI for Open Calibre Store.
"""

from qt.core import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QAbstractItemView,
    QLineEdit,
    QPlainTextEdit,
    QLabel,
    QSpinBox,
    QMessageBox,
    QThread,
    pyqtSignal
)

import urllib.request
from calibre.utils.config import JSONConfig


CONFIG = JSONConfig(
    "plugins/OpenCalibreStore"
)


def get_config():

    return CONFIG


class ConnectionTestWorker(QThread):

    """
    Runs one or more OPDS connectivity checks on a background
    thread so the Customize dialog never blocks the UI.

    targets: list of (host, port, https) tuples.
    Emits result_ready(index, ok, message) as each target
    finishes, in the same order as `targets`. The built-in
    QThread.finished signal fires once all targets are done
    (or the thread was asked to stop early).
    """

    result_ready = pyqtSignal(int, bool, str)

    def __init__(self, targets, timeout=5, parent=None):

        QThread.__init__(self, parent)

        self.targets = targets
        self.timeout = timeout

    def run(self):

        for index, (host, port, https) in enumerate(self.targets):

            if self.isInterruptionRequested():
                break

            ok, message = self._test(host, port, https)
            self.result_ready.emit(index, ok, message)

    def _test(self, host, port, https):

        protocol = "https" if https else "http"
        url = f"{protocol}://{host}:{port}/opds"

        try:

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Calibre Open Calibre Store Test"
                }
            )

            with urllib.request.urlopen(request, timeout=self.timeout) as response:

                content_type = response.headers.get("Content-Type", "")

                if response.status == 200:
                    return True, content_type

                return False, f"HTTP status: {response.status}"

        except Exception as err:

            return False, str(err)


class ConfigWidget(QWidget):

    def __init__(self):

        QWidget.__init__(self)

        self.servers = CONFIG.get("servers", [])

        # In-memory only: (host, port) -> True/False.
        # Not persisted; cleared each time the dialog opens.
        self.server_status = {}

        self._worker = None
        self._on_finished = None
        self._results = []
        self._worker_total = 0
        self._worker_done = 0
        self._closing = False

        self.setup_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def setup_ui(self):

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Configured Open Calibre Servers:"))

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.list)

        # --- Manage existing list: retest / remove inaccessible ---

        manage_row = QHBoxLayout()

        self.retest_selected_btn = QPushButton("Retest Selected")
        self.retest_all_btn = QPushButton("Retest All")
        self.remove_inaccessible_btn = QPushButton("Remove Inaccessible")

        self.retest_selected_btn.clicked.connect(self.retest_selected)
        self.retest_all_btn.clicked.connect(self.retest_all)
        self.remove_inaccessible_btn.clicked.connect(self.remove_inaccessible)

        manage_row.addWidget(self.retest_selected_btn)
        manage_row.addWidget(self.retest_all_btn)
        manage_row.addWidget(self.remove_inaccessible_btn)

        layout.addLayout(manage_row)

        # --- Add a single server ---

        form = QHBoxLayout()

        self.host = QLineEdit()
        self.host.setPlaceholderText("Server IP or hostname")

        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(8080)

        form.addWidget(self.host)
        form.addWidget(self.port)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        self.add_btn = QPushButton("Add Server")
        self.test_btn = QPushButton("Test Server")
        self.remove_btn = QPushButton("Remove Selected")

        self.add_btn.clicked.connect(self.add_server)
        self.test_btn.clicked.connect(self.test_server)
        self.remove_btn.clicked.connect(self.remove_server)

        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.test_btn)
        buttons.addWidget(self.remove_btn)

        layout.addLayout(buttons)

        # --- Bulk add servers ---

        layout.addWidget(
            QLabel(
                "Bulk Add Servers "
                "(one per line, e.g. 192.168.1.10:8080 "
                "or https://calibre.example.com:8081 "
                "\u2014 lines starting with # are ignored):"
            )
        )

        self.bulk_input = QPlainTextEdit()
        self.bulk_input.setPlaceholderText(
            "192.168.1.10:8080\n"
            "192.168.1.11\n"
            "https://calibre.example.com:8081"
        )
        self.bulk_input.setMaximumHeight(100)
        layout.addWidget(self.bulk_input)

        self.bulk_btn = QPushButton("Bulk Add && Test")
        self.bulk_btn.clicked.connect(self.bulk_add_and_test)
        layout.addWidget(self.bulk_btn)

        # --- Status line (shows progress while a test is running) ---

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self._action_buttons = [
            self.add_btn,
            self.test_btn,
            self.remove_btn,
            self.retest_selected_btn,
            self.retest_all_btn,
            self.remove_inaccessible_btn,
            self.bulk_btn
        ]

        self.refresh_list()

        self.setLayout(layout)

    def closeEvent(self, event):

        self._closing = True

        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()

        QWidget.closeEvent(self, event)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def display_name(self, server):

        return f"{server.get('host')}:{server.get('port')}"

    def _status_suffix(self, server):

        key = (server.get("host"), server.get("port"))
        status = self.server_status.get(key)

        if status is True:
            return "  \u2014  OK"

        if status is False:
            return "  \u2014  UNREACHABLE"

        return ""

    def refresh_list(self):

        self.list.clear()

        for server in self.servers:
            self.list.addItem(
                self.display_name(server) + self._status_suffix(server)
            )

    # ------------------------------------------------------------------
    # Background connectivity testing
    # ------------------------------------------------------------------

    def _set_busy(self, busy, message=""):

        for btn in self._action_buttons:
            btn.setEnabled(not busy)

        self.list.setEnabled(not busy)
        self.status_label.setText(message)

    def _run_tests(self, targets, on_finished):

        """
        targets: list of dicts with host/port/https keys.
        on_finished: callable(results) called on the UI thread
        once all targets have been tested, where results is a
        list of (ok, message) tuples aligned with targets.
        """

        if self._worker is not None and self._worker.isRunning():

            QMessageBox.information(
                self,
                "Busy",
                "A connectivity test is already running. "
                "Please wait for it to finish."
            )

            return

        if not targets:
            on_finished([])
            return

        self._results = [(False, "cancelled")] * len(targets)
        self._on_finished = on_finished
        self._worker_total = len(targets)
        self._worker_done = 0

        self._set_busy(True, f"Testing 0/{self._worker_total}...")

        self._worker = ConnectionTestWorker(
            [
                (t["host"], t["port"], t.get("https", False))
                for t in targets
            ]
        )

        self._worker.result_ready.connect(self._on_single_result)
        self._worker.finished.connect(self._on_all_finished)
        self._worker.start()

    def _on_single_result(self, index, ok, message):

        if self._closing:
            return

        self._results[index] = (ok, message)
        self._worker_done += 1

        self._set_busy(
            True,
            f"Testing {self._worker_done}/{self._worker_total}..."
        )

    def _on_all_finished(self):

        results = self._results
        callback = self._on_finished

        self._worker = None
        self._on_finished = None

        if self._closing:
            return

        self._set_busy(False, "")

        if callback:
            callback(results)

    # ------------------------------------------------------------------
    # Single server: add / test / remove
    # ------------------------------------------------------------------

    def add_server(self):

        host = self.host.text().strip()

        if not host:

            QMessageBox.warning(
                self,
                "Missing Host",
                "Enter an IP address or hostname."
            )

            return

        server = {
            "host": host,
            "port": self.port.value(),
            "enabled": True,
            "https": False
        }

        self.servers.append(server)
        self.refresh_list()
        self.host.clear()

    def test_server(self):

        host = self.host.text().strip()
        port = self.port.value()

        if not host:

            QMessageBox.warning(
                self,
                "Missing Host",
                "Enter an IP address or hostname first."
            )

            return

        target = {"host": host, "port": port, "https": False}

        def finished(results):

            ok, message = results[0]
            url = f"http://{host}:{port}/opds"

            if ok:

                QMessageBox.information(
                    self,
                    "Server OK",
                    (
                        "Open Calibre server responded.\n\n"
                        f"URL:\n{url}\n\n"
                        f"Type:\n{message}"
                    )
                )

            else:

                QMessageBox.critical(
                    self,
                    "Connection Failed",
                    (
                        f"Could not reach:\n\n{url}\n\n"
                        f"Error:\n{message}"
                    )
                )

        self._run_tests([target], finished)

    def remove_server(self):

        row = self.list.currentRow()

        if row >= 0:

            server = self.servers[row]
            key = (server.get("host"), server.get("port"))
            self.server_status.pop(key, None)

            del self.servers[row]
            self.refresh_list()

    # ------------------------------------------------------------------
    # Retesting servers already in the list
    # ------------------------------------------------------------------

    def _retest_rows(self, rows):

        rows = list(rows)
        targets = [self.servers[row] for row in rows]

        def finished(results):

            display_results = []

            for row, (ok, _msg) in zip(rows, results):

                server = self.servers[row]
                key = (server.get("host"), server.get("port"))
                self.server_status[key] = ok

                display_results.append((self.display_name(server), ok))

            self.refresh_list()

            reachable = sum(1 for _, ok in display_results if ok)
            unreachable = len(display_results) - reachable

            summary = "\n".join(
                f"{'OK ' if ok else 'FAIL'}  {name}"
                for name, ok in display_results
            )

            QMessageBox.information(
                self,
                "Retest Complete",
                (
                    f"{reachable} reachable, "
                    f"{unreachable} unreachable.\n\n{summary}"
                )
            )

        self._run_tests(targets, finished)

    def retest_selected(self):

        rows = sorted(set(
            index.row() for index in self.list.selectedIndexes()
        ))

        if not rows:

            QMessageBox.information(
                self,
                "No Selection",
                "Select one or more servers in the list first."
            )

            return

        self._retest_rows(rows)

    def retest_all(self):

        if not self.servers:

            QMessageBox.information(
                self,
                "No Servers",
                "There are no configured servers to test."
            )

            return

        self._retest_rows(range(len(self.servers)))

    def remove_inaccessible(self):

        if not self.servers:

            QMessageBox.information(
                self,
                "No Servers",
                "There are no configured servers to test."
            )

            return

        confirm = QMessageBox.question(
            self,
            "Remove Inaccessible Servers",
            (
                f"This will test all {len(self.servers)} configured "
                "server(s) and permanently remove any that fail to "
                "respond.\n\nContinue?"
            ),
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        targets = list(self.servers)

        def finished(results):

            keep = []
            removed_names = []

            for server, (ok, _msg) in zip(targets, results):

                key = (server.get("host"), server.get("port"))

                if ok:
                    self.server_status[key] = True
                    keep.append(server)
                else:
                    self.server_status.pop(key, None)
                    removed_names.append(self.display_name(server))

            self.servers = keep
            self.refresh_list()

            if removed_names:

                QMessageBox.information(
                    self,
                    "Removed Inaccessible Servers",
                    "Removed:\n\n" + "\n".join(removed_names)
                )

            else:

                QMessageBox.information(
                    self,
                    "All Servers Reachable",
                    (
                        "No servers were removed; all configured "
                        "servers responded."
                    )
                )

        self._run_tests(targets, finished)

    # ------------------------------------------------------------------
    # Bulk add + test
    # ------------------------------------------------------------------

    def _parse_server_line(self, line):

        line = line.strip()

        if not line or line.startswith("#"):
            return None

        https = False

        if "://" in line:
            scheme, line = line.split("://", 1)
            https = scheme.strip().lower() == "https"

        # Drop any trailing path, e.g. "host:8080/opds"
        line = line.split("/", 1)[0]

        if ":" in line:

            host, port_str = line.rsplit(":", 1)

            try:
                port = int(port_str)
            except ValueError:
                host = line
                port = 8080

        else:

            host = line
            port = 8080

        host = host.strip()

        if not host:
            return None

        return {
            "host": host,
            "port": port,
            "https": https,
            "enabled": True
        }

    def bulk_add_and_test(self):

        text = self.bulk_input.toPlainText()
        lines = text.splitlines()

        existing = {
            (s.get("host"), s.get("port")) for s in self.servers
        }

        candidates = []
        skipped_duplicates = 0

        for line in lines:

            parsed = self._parse_server_line(line)

            if not parsed:
                continue

            key = (parsed["host"], parsed["port"])

            if key in existing:
                skipped_duplicates += 1
                continue

            existing.add(key)
            candidates.append(parsed)

        if not candidates:

            message = "No new servers to add."

            if skipped_duplicates:
                message += (
                    f"\n\n({skipped_duplicates} duplicate "
                    "line(s) skipped.)"
                )

            QMessageBox.information(self, "Bulk Add", message)
            return

        def finished(results):

            display_results = []

            for server, (ok, _msg) in zip(candidates, results):

                self.servers.append(server)

                key = (server["host"], server["port"])
                self.server_status[key] = ok

                display_results.append((self.display_name(server), ok))

            self.refresh_list()
            self.bulk_input.clear()

            reachable = sum(1 for _, ok in display_results if ok)
            unreachable = len(display_results) - reachable

            summary = "\n".join(
                f"{'OK ' if ok else 'FAIL'}  {name}"
                for name, ok in display_results
            )

            extra = ""

            if skipped_duplicates:
                extra = (
                    f"\n\n({skipped_duplicates} duplicate "
                    "line(s) skipped.)"
                )

            QMessageBox.information(
                self,
                "Bulk Add Complete",
                (
                    f"Added {len(candidates)} server(s): "
                    f"{reachable} reachable, {unreachable} unreachable."
                    f"{extra}\n\n{summary}"
                )
            )

        # Servers are only appended to self.servers inside the
        # finished callback above, once results are known - this
        # keeps the list free of untested/duplicate entries if the
        # dialog is used again before a run completes.
        self._run_tests(candidates, finished)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_settings(self):

        CONFIG["servers"] = self.servers
        CONFIG.commit()
