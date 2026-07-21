"""Disabled hosted cloud proxy compatibility surface for Cloud CE."""


async def get_proxy_client(*args, **kwargs):
    del args, kwargs
    raise RuntimeError("The hosted cloud proxy is not available in Cloud CE")
