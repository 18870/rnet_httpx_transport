# rnet_httpx_transport
An httpx.AsyncTransport for [rnet](https://github.com/0x676e67/rnet) library.


## Usage
See example.py.

Tested with httpx 0.28.1 and rnet 2.4.2 and 3.0.0rc


## Not supported features
- No sync transport (im lazy)
- Only `pool` and `read` timeout works.
- Auth, redirects aren't tested, may not work at all.