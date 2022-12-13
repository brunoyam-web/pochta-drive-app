import re

re_file_link = re.compile(r"^https:\/\/.*/d/(.*)/.*$")
re_code = re.compile(r"code=(.*)&")
"""RegEx for extracting code from google auth response from frontend. We need second parameter"""
