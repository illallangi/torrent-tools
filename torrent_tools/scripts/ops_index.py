from requests import HTTPError, get as http_get
from loguru import logger

from click import STRING, command, option

from json import dumps

from yarl import URL

from .. import ORPHEUS_ENDPOINT, USER_AGENT


@command()
@option(
    "--orpheus-api-key",
    envvar="ORPHEUS_API_KEY",
    type=STRING,
)
@option(
    "--orpheus-endpoint",
    required=False,
    default=ORPHEUS_ENDPOINT,
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
    orpheus_api_key,
    orpheus_endpoint,
    user_agent,
):
    assert isinstance(orpheus_endpoint, URL)

    get = {
        "url": orpheus_endpoint
        / "ajax.php"
        % {
            "action": "index",
        },
        "headers": {
            "User-Agent": user_agent,
            "Authorization": f"token {orpheus_api_key}",
        },
    }

    logger.trace(get)
    try:
        r = http_get(**get)
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
    if "status" not in result or result["status"] != "success":
        logger.error(f'Status of {result.get("status")}, expected success')
        return
    if "response" not in result or result["response"] is None:
        logger.error("No response received")
        return

    result = result["response"]
    print(dumps(result))


if __name__ == "__main__":
    cli()
