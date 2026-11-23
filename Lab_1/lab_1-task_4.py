import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

async def app(scope, receive, send):
    if scope['type'] != 'http':
        return

    method = scope["method"]
    path = scope["path"]

    if method == "GET" and path == "/":
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"text/plain"),
            ],
        })

        await send({
            "type": "http.response.body",
            "body": b"200 OK\n",
        })

    else:
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [
                (b"content-type", b"text/plain"),
            ],
        })

        await send({
            "type": "http.response.body",
            "body": b"404 Not Found\n",
        })


if __name__ == '__main__':
    config = Config()
    config.bind = ["0.0.0.0:4433"]
    config.quic_bind = ["0.0.0.0:4433"]
    config.certfile = "server.crt"
    config.keyfile = "server.key"
    config.alpn_protocols = ["h3", "h2", "http/1.1"]
    asyncio.run(serve(app, config))