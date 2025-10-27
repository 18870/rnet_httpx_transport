from typing import AsyncIterator

import httpx
import rnet


class RnetAsyncByteStream(httpx.AsyncByteStream):
    def __init__(self, response: rnet.Response) -> None:
        self.response = response
        self.streamer = response.stream()

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self.streamer:
            yield chunk

    async def aclose(self) -> None:
        await self.response.close()


class RnetAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(
        self,
        impersonate: rnet.Impersonate | rnet.ImpersonateOption | None = None,
        proxies: str | list[rnet.Proxy] | None = None,
        **kwargs,
    ) -> None:
        """
        See rnet.Client for available kwargs
        """

        if isinstance(proxies, str):
            proxies = [rnet.Proxy.all(proxies)]

        self.client = rnet.Client(
            impersonate=impersonate,
            allow_redirects=False,
            cookie_store=False,
            proxies=proxies,
            **kwargs,
        )

    @staticmethod
    def _map_headers(headers: httpx.Headers) -> rnet.HeaderMap:
        rnet_headers = rnet.HeaderMap()
        for k, v in headers.items():
            if k == "user-agent" and v == httpx._client.USER_AGENT:
                # ignore default httpx user-agent to let rnet set its own
                continue
            rnet_headers.append(k, v)
        return rnet_headers

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        request_params = {
            "method": getattr(rnet.Method, request.method),
            "url": str(request.url),
            "headers": self._map_headers(request.headers),
            "body": request.content,
        }

        timeouts = request.extensions.get("timeout", {})
        request_params["timeout"] = timeouts.get("pool")
        request_params["read_timeout"] = timeouts.get("read")

        try:
            resp = await self.client.request(**request_params)
        except (
            rnet.exceptions.DNSResolverError,
            rnet.exceptions.BodyError,
            rnet.exceptions.BuilderError,
            rnet.exceptions.RedirectError,
            rnet.exceptions.RequestError,
            rnet.exceptions.UpgradeError,
            rnet.exceptions.MIMEParseError,
            rnet.exceptions.StatusError,
        ) as e:
            raise httpx.RequestError(message=e.args, request=request) from e
        except (
            rnet.exceptions.ConnectionError,
            rnet.exceptions.ConnectionResetError,
        ) as e:
            raise httpx.ConnectError(message=e.args, request=request) from e
        except rnet.exceptions.DecodingError as e:
            raise httpx.DecodingError(message=e.args, request=request) from e
        except rnet.exceptions.TimeoutError as e:
            raise httpx.TimeoutException(message=e.args, request=request) from e
        except rnet.exceptions.URLParseError as e:
            raise httpx.InvalidURL(message=e.args, request=request) from e

        return httpx.Response(
            status_code=resp.status,
            headers=[(k, v) for k, v in resp.headers.items()],
            stream=RnetAsyncByteStream(resp),
            request=request,
        )
