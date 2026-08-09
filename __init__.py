from calibre.customize import StoreBase


class OpenCalibreStore(StoreBase):

    name = "Open Calibre Store"

    description = (
        "Search and download books from "
        "your Open Calibre Content Servers "
        "through Calibre Get Books."
    )

    author = "ketzah"

    version = (1, 2, 1)

    actual_plugin = "{}.store:OpenCalibreStore".format(__name__)

    minimum_calibre_version = (9, 0, 0)

    def is_customizable(self):
        return True

    def config_widget(self):
        from .config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
