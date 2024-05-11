import asyncio
import sys


class HttpRequest:

    def __init__(self):

        self.method = None  # GET, POST, etc.
        self.path = None
        self.protocol = None
        self.headers = {}
        self.body = bytearray()
        self.body_len = None
        self.part = "request"

    def parse_line(self, line: bytes):

        if self.part == "request":
            data = line.strip().split(b" ", 2)
            self.method, self.path, self.protocol = data
            self.part = "headers"

        elif self.part == "headers":
            if line.strip() != b"":
                key, value = line.split(b":", 1)
                self.headers[key.strip()] = value.strip()
                if key.lower() == b"content-length":
                    self.body_len = int(value)
            else:
                self.part = "body"

        elif self.part == "body":
            if (self.body_len is not None) and (len(self.body) >= self.body_len):
                return
            if line.strip() != b"":
                self.body.extend(line.strip())


