from json import dumps
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
    release_type_names,
    original,
    remaster_year=False,
    *args,
    **kwargs,
):
    get = {
        "url": endpoint
        / "ajax.php"
        % {
            "action": "torrent",
            "hash": hash.lower(),
        },
        "headers": {
            "User-Agent": user_agent,
            "Authorization": api_key,
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
            release_type_names,
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
    if "status" not in result or result["status"] != "success":
        logger.error(f'Status of {result.get("status")}, expected success')
        return name
    if "response" not in result or result["response"] is None:
        logger.error("No response received")
        return name

    if original:
        return result["response"]["torrent"]["filePath"]

    result = {
        **{k: v for k, v in result["response"].items()},
        "group": {
            **{k: v for k, v in result["response"]["group"].items()},
            "releaseTypeName": release_type_names.get(
                result["response"]["group"]["releaseType"],
                f'Unknown Release Type {result["response"]["group"]["releaseType"]} - may be {result["response"]["group"].get("releaseTypeName", "fuck")}',
            ),
        },
        "catalogueNumber": (
            " {"
            + (
                result["response"]["group"]["catalogueNumber"]
                if result["response"]["torrent"]["remasterCatalogueNumber"]
                in [0, None, ""]
                else result["response"]["torrent"]["remasterCatalogueNumber"]
            )
            .replace("(", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
            .replace("{", "")
            .replace("}", "")
            .replace("-", "")
            .replace(" ", "")
            + "}"
        ).replace(" {}", ""),
        "format": (
            " ["
            + " ".join(
                [
                    v
                    for v in [
                        result["response"]["torrent"]["media"],
                        result["response"]["torrent"]["format"],
                        result["response"]["torrent"]["encoding"],
                    ]
                    if v is not None
                ]
            )
            .replace(" Lossless", "")
            .replace(" (VBR)", "")
            + "]"
        ),
        "remaster": (
            " (" + result["response"]["torrent"]["remasterTitle"] + ")"
        ).replace(" ()", ""),
    }

    if result["group"]["releaseTypeName"] in [
        "Compilation",
        "Soundtrack",
    ]:
        return clean_filename(
            " - ".join(
                [
                    result["group"]["releaseTypeName"],
                    str(
                        result["group"]["year"]
                        if not remaster_year
                        and result["torrent"]["remasterYear"] in [0, None, ""]
                        else result["torrent"]["remasterYear"]
                    ),
                    result["group"]["name"],
                ]
            )
            + result["remaster"]
            + result["catalogueNumber"]
            + result["format"]
        )

    if result["group"]["releaseTypeName"] in [
        "Album",
        "Anthology",
        "Bootleg",
        "Concert Recording",
        "DJ Mix",
        "EP",
        "Live Album",
        "Mixtape",
        "Remix",
        "Single",
    ]:
        return clean_filename(
            " - ".join(
                [
                    first(result["group"]["musicInfo"]["artists"])["name"],
                    result["group"]["releaseTypeName"],
                    str(result["group"]["year"]),
                    result["group"]["name"],
                ]
            )
            + result["remaster"]
            + result["catalogueNumber"]
            + result["format"]
        )

    logger.warning(f'Unhandled Release Type "{result["group"]["releaseTypeName"]}"')
    return name
