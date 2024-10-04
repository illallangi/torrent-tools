from requests import HTTPError, post as http_post
from loguru import logger

from click import STRING, command, option

from json import dumps

from yarl import URL

from .. import BTN_ENDPOINT, USER_AGENT


@command()
@option(
    "--btn-api-key",
    envvar="BTN_API_KEY",
    type=STRING,
)
@option(
    "--btn-endpoint",
    required=False,
    default=BTN_ENDPOINT,
    show_default=True,
    callback=lambda _1, _2, x: x if isinstance(x, URL) else URL(x),
)
@option(
    "--user-agent",
    required=False,
    default=USER_AGENT,
    show_default=True,
)
def cli(
    btn_api_key,
    btn_endpoint,
    user_agent,
):
    assert isinstance(btn_endpoint, URL)

    post = {
        "url": btn_endpoint,
        "json": {
            "method": "userInfo",
            "params": [btn_api_key],
            "id": 1,
        },
        "headers": {
            "Authorization": f"token {btn_api_key}",
        },
    }

    logger.trace(post)
    try:
        r = http_post(**post)
        r.raise_for_status()
        assert r.headers.get(
            "content-type"
        ).startswith(
            "application/json"
        ), f'content-type was {r.headers.get("content-type")}, expected application/json'
        result = r.json()
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        return

    logger.debug("Received {0} bytes from API".format(len(r.content)))
    logger.trace(
        {
            "headers": r.headers,
            "body": result,
        },
    )

    if "error" in result:
        logger.error(f'Error {result.get("error")}, expected none')
        return
    if "result" not in result or result["result"] is None:
        logger.error("No result received")
        return

    result = result["result"]
    print(dumps(result))


if __name__ == "__main__":
    cli()
