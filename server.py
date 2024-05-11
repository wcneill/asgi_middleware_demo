import sys
import asyncio
from http_helpers import HttpRequest
from services import echo_app

ports_dict = {}


class AsgiServerBase:
    def __init__(self):
        print(f" {type(self).__name__} started...")

    def create_scope(self, request: HttpRequest) -> dict:
        raise NotImplementedError("ServerBase is an abstract class. Please implement this method in your class.")

    def create_event(self, body: str, more_body: bool) -> dict:
        return {
            "type": "http.request",
            "body": body,
            "more_body": more_body
        }

    def __call__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        raise NotImplementedError("ServerBase is meant to serve as an abstract base and is not for actual service.")



class HttpParsingServer(AsgiServerBase):

    def __init__(self):
        super().__init__()


    async def __call__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):

        # These queues are used for messaging between the app.
        to_app = asyncio.Queue()
        from_app = asyncio.Queue()
        request = HttpRequest()

        # Read and parse the HTTP request from the client, one line at a time.
        more_body = True
        while not reader.at_eof():
            line = await reader.readline()
            request.parse_line(line)

            if request.part == "body":
                more_body = len(request.body) < request.body_len

                # Here is where we fill up the event message queue with the body of the client's request!
                await to_app.put(self.create_event(request.body.copy(), more_body))

            if not more_body:
                break

        # Form the response that the request was received.
        response = f"\n\tStatus: 200 " \
                   f"\n\tprotocol: {request.protocol}" \
                   f"\n\tbody-length: {request.body_len}\n"

        # Send the response back to the client.
        writer.write(response.encode())

        # Time to pass things along with the app. Starting with the scope dict.
        scope = self.create_scope(request)
        await echo_app(scope, to_app.get, from_app.put)

        # Now we wait and receive a response from the app.
        while True:
            message = await from_app.get()
            if message["type"] == "http.response.start":
                writer.write(b"\n\tapp has received your request and is processing.")
            elif message["type"] == "http.response.body":
                if message["body"] is not None:
                    writer.write(b'\n\tThe app would like to return this to you: ' + message["body"])
                if not message.get("more_body", False):
                    break

        writer.write(b"\n\tThe application has finished running.")
        writer.write_eof()
        writer.close()

    def create_scope(self, request: HttpRequest):
        return {
            "type": "http",
            "method": request.method,
            "raw_path": request.path,
            "path": request.path.decode(),
            "headers": request.headers
        }


async def main(server, host, port):
    if server == "http_parser":
        server_object = HttpParsingServer()
    else:
        raise ValueError(f"Unexpected Server type: {server}")

    server = await asyncio.start_server(server_object, host, port)
    await server.serve_forever()

if __name__ == "__main__":
    server, host, port = sys.argv[1], sys.argv[2], sys.argv[3]
    asyncio.run(main(server, host, port))
