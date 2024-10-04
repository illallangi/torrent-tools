from json import dumps, loads
from more_itertools import first
from time import sleep
from loguru import logger
from requests import HTTPError
from .clean_filename import clean_filename


def get_name(
    hash,
    name,
    endpoint,
    api_key,
    user_agent,
    session,
    *args,
    **kwargs,
):
    get = {
        "url": endpoint
        / "tor"
        / "js"
        / "loadSearchJSONbasic.php"
        % {
            "tor[hash]": hash.lower(),
        },
        "headers": {
            "User-Agent": user_agent,
        },
        "cookies": {
            "mam_id": api_key,
        },
    }

    logger.trace(get)
    try:
        r = session.get(**get)
        r.raise_for_status()
        assert r.headers.get(
            "content-type"
        ).startswith(
            "application/json"
        ), f'content-type was {r.headers.get("content-type")}, expected application/json'
        result = r.json()
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}, sleeping 60 seconds")
        logger.trace(r.text)
        sleep(60)
        return get_name(
            hash,
            name,
            endpoint,
            api_key,
            user_agent,
            session,
            *args,
            **kwargs,
        )
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        return name

    logger.trace("Received {0} bytes from API".format(len(r.content)))
    logger.trace(
        dumps(
            {
                "headers": {k: r.headers[k] for k in r.headers},
                "body": result,
            },
            indent=2,
        ),
    )
    if "error" in result:
        logger.error(f'Error {result.get("error")}, expected none')
        return name
    if "total" not in result or result["total"] != 1:
        logger.error(f'Total of {result.get("total")}, expected 1')
        return name
    if "found" not in result or result["found"] != 1:
        logger.error(f'Found of {result.get("found")}, expected 1')
        return name
    if "data" not in result or result["data"] is None or len(result["data"]) != 1:
        logger.error("No data received")
        return name

    authors = list(loads(first(result["data"])["author_info"]).values())
    return clean_filename(
        " - ".join(
            [
                "{} and {}".format(", ".join(authors[:-1]), authors[-1])
                if len(authors) > 1
                else authors[0],
                first(result["data"])["title"],
            ],
        )
        + f" {{{first(result['data'])['id']}}}",
    )
    return name
