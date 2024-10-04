from os.path import splitext
from re import compile as re_compile, Pattern
from click import STRING, command, option, INT, prompt, IntRange
from .. import (
    CONFIG,
    DELUGE_PORT,
    DELUGE_USERNAME,
    FILTER,
    ORPHEUS_ENDPOINT,
    REDACTED_ENDPOINT,
    MAM_ENDPOINT,
    USER_AGENT,
    RELEASE_TYPE_NAMES,
)
from ..gazelle import get_name as gazelle_get_name
from ..mam import get_name as mam_get_name
from yarl import URL
from loguru import logger
from tqdm import tqdm
from requests_cache import CachedSession
from datetime import timedelta
from deluge_client import DelugeRPCClient


@command()
@option(
    "--orpheus-api-key",
    required=True,
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
    "--redacted-api-key",
    required=True,
    envvar="REDACTED_API_KEY",
    type=STRING,
)
@option(
    "--redacted-endpoint",
    required=False,
    default=REDACTED_ENDPOINT,
    show_default=True,
    callback=lambda _1, _2, x: x if isinstance(x, URL) else URL(x),
)
@option(
    "--mam-api-key",
    required=True,
    envvar="MAM_API_KEY",
    type=STRING,
)
@option(
    "--mam-endpoint",
    required=False,
    default=MAM_ENDPOINT,
    show_default=True,
    callback=lambda _1, _2, x: x if isinstance(x, URL) else URL(x),
)
@option(
    "--deluge-host",
    required=True,
    envvar="DELUGE_HOST",
)
@option(
    "--deluge-port",
    required=False,
    default=DELUGE_PORT,
    show_default=True,
    type=INT,
)
@option(
    "--deluge-username",
    required=False,
    default=DELUGE_USERNAME,
    show_default=True,
)
@option(
    "--deluge-password",
    required=True,
    envvar="DELUGE_PASSWORD",
)
@option(
    "--user-agent",
    required=False,
    default=USER_AGENT,
    show_default=True,
)
@option(
    "--filter",
    required=False,
    default=FILTER,
    show_default=True,
    callback=lambda _1, _2, x: x if isinstance(x, Pattern) else re_compile(x),
)
@option(
    "--label",
    required=False,
    default=FILTER,
    show_default=True,
    callback=lambda _1, _2, x: x if isinstance(x, Pattern) else re_compile(x),
)
@option(
    "--tracker",
    required=False,
    default=FILTER,
    show_default=True,
    callback=lambda _1, _2, x: x if isinstance(x, Pattern) else re_compile(x),
)
@option(
    "--config",
    required=False,
    default=CONFIG,
    show_default=True,
)
@option(
    "--original",
    required=False,
    default=False,
    show_default=True,
    is_flag=True,
)
@option(
    "--dryrun",
    required=False,
    default=False,
    show_default=True,
    is_flag=True,
)
def cli(
    deluge_host,
    deluge_port,
    deluge_username,
    deluge_password,
    orpheus_endpoint,
    orpheus_api_key,
    redacted_endpoint,
    redacted_api_key,
    mam_endpoint,
    mam_api_key,
    filter,
    label,
    tracker,
    config,
    dryrun,
    **kwargs,
):
    logger.remove()
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

    client = DelugeRPCClient(
        deluge_host,
        deluge_port,
        deluge_username,
        deluge_password,
    )
    assert isinstance(filter, Pattern), "filter is not a Pattern"
    assert isinstance(label, Pattern), "label is not a Pattern"
    assert isinstance(orpheus_endpoint, URL), "orpheus_endpoint is not a URL"
    assert isinstance(redacted_endpoint, URL), "redacted_endpoint is not a URL"

    with CachedSession(
        config,
        cache_control=False,
        expire_after=timedelta(days=2),
        allowable_methods=[
            "GET",
        ],
        backend="filesystem",
    ) as session:
        logger.trace(f"Using cache dir {session.cache.cache_dir}")

        tracker_callbacks = {
            "opsfet.ch": lambda hash, name: gazelle_get_name(
                hash=hash,
                name=name,
                api_key=orpheus_api_key,
                endpoint=orpheus_endpoint,
                session=session,
                release_type_names=RELEASE_TYPE_NAMES["opsfet.ch"],
                **kwargs,
            ),
            "flacsfor.me": lambda hash, name: gazelle_get_name(
                hash=hash,
                name=name,
                api_key=redacted_api_key,
                endpoint=redacted_endpoint,
                session=session,
                release_type_names=RELEASE_TYPE_NAMES["flacsfor.me"],
                **kwargs,
            ),
            "myanonamouse.net": lambda hash, name: mam_get_name(
                hash=hash,
                name=name,
                api_key=mam_api_key,
                endpoint=mam_endpoint,
                session=session,
                release_type_names=RELEASE_TYPE_NAMES["myanonamouse.net"],
                **kwargs,
            ),
        }

        client.connect()
        if not client.connected:
            raise Exception()

        torrent_status = [
            a
            for a in client.call(
                "core.get_torrents_status",
                {},
                [
                    "hash",
                    "name",
                    "tracker_host",
                    "label",
                ],
            ).values()
            if filter.match(a[b"name"].decode("utf-8"))
            and label.match(a[b"label"].decode("utf-8"))
            and tracker.match(a[b"tracker_host"].decode("utf-8"))
        ]

        for directory in tqdm(
            [
                {
                    "name": b,
                    "torrents": {
                        a[b"tracker_host"].decode("utf-8"): {
                            "hash": a[b"hash"].decode("utf-8"),
                            "label": a[b"label"].decode("utf-8"),
                        }
                        for a in torrent_status
                        if a[b"name"].decode("utf-8") == b
                    },
                }
                for b in sorted(
                    {c[b"name"].decode("utf-8") for c in torrent_status},
                )
            ],
            leave=False,
        ):
            if [t for t in directory["torrents"] if t not in tracker_callbacks]:
                for tracker in [
                    t for t in directory["torrents"] if t not in tracker_callbacks
                ]:
                    logger.error(
                        f"Unsupported tracker {tracker}, skipping {directory['name']}"
                    )
                continue

            candidates = sorted(
                {
                    tracker_callbacks[tracker](
                        hash=directory["torrents"][tracker]["hash"],
                        name=directory["name"],
                    )
                    for tracker in directory["torrents"]
                },
                key=len,
                reverse=True,
            )
            if splitext(directory["name"])[0] in candidates:
                logger.info(f"{directory['name']} is a candidate, no action required")
                continue

            logger.info(
                f"'{directory['name']}' ({len(directory['torrents'])} torrents) has {len(candidates)} candidate(s):"
            )
            for index, candidate in enumerate(candidates):
                logger.info(f" {index + 1}: '{candidate}'")

            result = 1
            if len(candidates) > 1:
                result = prompt(
                    "Select a candidate, 0 to skip",
                    type=IntRange(min=0, max=len(candidates)),
                    default=1,
                )

            if result == 0:
                logger.info(" - Skipping")
                continue

            for hash in [
                directory["torrents"][a]["hash"] for a in directory["torrents"]
            ]:
                files = {
                    p[b"index"]: p[b"path"].decode("utf-8")
                    for p in client.call(
                        "core.get_torrents_status",
                        {b"hash": hash},
                        ["files"],
                    )[hash.encode("utf8")][b"files"]
                }
                if len(files) == 1:
                    target = "".join(
                        [
                            candidates[result - 1],
                            splitext(files[list(files.keys())[0]])[1],
                        ],
                    )
                    logger.info(f" - Renaming {hash} to {target}")
                    if not dryrun:
                        client.call(
                            "core.rename_files",
                            hash,
                            [
                                (
                                    list(files.keys())[0],
                                    target.encode("utf-8"),
                                ),
                            ],
                        )
                else:
                    logger.info(f" - Renaming {hash} to {candidates[result - 1]}")
                    if not dryrun:
                        client.call(
                            "core.rename_folder",
                            hash,
                            directory["name"],
                            candidates[result - 1],
                        )

            for hash in [
                directory["torrents"][a]["hash"] for a in directory["torrents"]
            ]:
                logger.info(f" - Rechecking {hash}")
                if not dryrun:
                    client.call(
                        "core.force_recheck",
                        [
                            hash,
                        ],
                    )


if __name__ == "__main__":
    cli()
