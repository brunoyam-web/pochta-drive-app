from dataclasses import dataclass


@dataclass
class File:
    name: str
    type: str
    fileId: str
    previewUrl: str = ""
    downloadUrl: str = ""

    def __init__(self, file) -> None:
        """Initialize File with GoogleDrive file object

        Args:
            file (GoogleDrie file):
            ```

            ```
        """
        self.name = file["name"]
        self.fileId = file["id"]
        self.type = file["mimeType"]
        self.previewUrl = file["webViewLink"]
        if "webContentLink" in file:
            self.downloadUrl = file["webContentLink"]
