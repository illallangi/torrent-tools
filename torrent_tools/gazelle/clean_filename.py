import unicodedata
import string

valid_filename_chars = "-_.()[]{} %s%s" % (string.ascii_letters, string.digits)


def clean_filename(
    filename,
    whitelist=valid_filename_chars,
    replace=[" Lossless", " (VBR)", " {}", " {[none]}", "."],
):
    # replace strings
    for r in replace:
        filename = filename.replace(r, "")
    # keep only valid ascii chars
    cleaned_filename = (
        unicodedata.normalize("NFKD", filename).encode("ASCII", "ignore").decode()
    )

    # keep only whitelisted chars
    cleaned_filename = "".join(c for c in cleaned_filename if c in whitelist).replace(
        "  ", " "
    )

    cleaned_filename = cleaned_filename.strip()

    return cleaned_filename
