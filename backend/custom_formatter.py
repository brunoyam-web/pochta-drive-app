from regexes import re_file_link


def get_fileid_from_link(link: str) -> str:
    """Get link in GDrive format and returns FileId from URL

    Args:
        link (str): link to file

    Returns:
        str: fileId
    """
    if re_file_link.fullmatch(link):
        return re_file_link.findall(link)[0]  # link.split("/")[5] also suits
    return None


if __name__ == "__main__":
    print(
        get_fileid_from_link(
            "https://drive.google.com/file/d/17W3Q13fB9rLXqJqTGC6fChXEsrzKrKz_/view?usp=share_link"
        )
    )
