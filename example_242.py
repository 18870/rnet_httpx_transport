import asyncio

import rnet
from httpx import AsyncClient, Timeout

from rnet_httpx_transport_242 import RnetAsyncTransport


async def main():
    transport = RnetAsyncTransport(
        impersonate=rnet.Impersonate.Safari18_5,
        proxies="http://127.0.0.1:7890",
    )

    async with AsyncClient(transport=transport) as client:
        response = await client.get(
            "https://tls.peet.ws/api/all",
            timeout=Timeout(timeout=10),
        )
        print(response.json())


if __name__ == "__main__":
    asyncio.run(main())
