import sys
import asyncio

async def communicate(host, port):
    reader, writer = await asyncio.open_connection(host, port)
    message = input("Enter a message: ")

    http_request = create_http(message)
    print("***********************************")
    print(f"Request being sent: \n{http_request}")
    print("***********************************")

    writer.write(http_request.encode())
    await writer.drain()

    while not reader.at_eof():
        response = await reader.read(-1)
        print(f"Recieved a response: {response.decode()}")

        if response == b"quit":
            reader.feed_eof()

    writer.close()
    await writer.wait_closed()


def create_http(message_body: str) -> str:
    return \
        f"GET / HTTP/1.1\r\n" \
        f"Host: localhost\r\n" \
        f"content-length: {len(message_body)}\r\n" \
        f"\r\n" \
        f"{message_body}\r\n"


if __name__ == "__main__":
    host, port = sys.argv[1], sys.argv[2]
    asyncio.run(communicate(host, port))
