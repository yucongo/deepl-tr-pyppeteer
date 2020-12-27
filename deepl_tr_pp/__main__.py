r"""Translate using deepl via pyppeteer.

for ["en", "de", "zh", "fr", "es", "pt", "it", "nl", "pl", "ru", "ja"]
"""
# pylint: disable=too-many-locals, too-many-branches, too-many-statements

from pathlib import Path
import re

# import sys
import atexit

# import asyncio
from itertools import zip_longest
from absl import app, flags
from docx import Document
import pyperclip
import logzero
from logzero import logger

from deepl_tr_pp import __version__
from deepl_tr_pp.deepl_tr_pp import LOOP, DEBUG, BROWSER
from deepl_tr_pp.deepl_tr_pp import deepl_tr_pp
from deepl_tr_pp.load_text import load_text
from deepl_tr_pp.gen_docx import gen_docx
from deepl_tr_pp.gen_docx1 import gen_docx1
from deepl_tr_pp.browse_filename import browse_filename

FLAGS = flags.FLAGS
_ = """
flags.DEFINE_string(
    "z-extra-info",
    "info",
    "supply text anywhere in the command line when --copyfrom=false",
)
# """
flags.DEFINE_string(
    "filepath",
    "",
    "source text filepath (relative or absolute), if not provided, clipboard content will be used as source text.",
    short_name="p",
)
flags.DEFINE_string(
    "from-lang", "en", "source language, default english)", short_name="f"
)
flags.DEFINE_string("to-lang", "zh", "target language, default chinese", short_name="t")

flags.DEFINE_boolean("dualtext", True, "dualtext or no dualtext output", short_name="d")
flags.DEFINE_bool("output-docx", True, "output docx or text", short_name="o")

flags.DEFINE_boolean("copyto", True, "copy the result to clipboard")
flags.DEFINE_boolean(
    "copyfrom",
    False,
    "copy from clipboard, default false, will attempt to browser for a filepath if copyfrom is set to false)",
)
flags.DEFINE_boolean("debug", False, "print debug messages.")
flags.DEFINE_boolean("version", False, "print version and exit")
# record all args
ARGS = [
    "filepath",
    "from-lang",
    "to-lang",
    "dualtext",
    "output-docx",
    "copyfrom",
    "copyto",
    "debug",
    "version",
]

# from shlex import split
# FLAGS(split("app --from-lang=en"))
# FLAGS.f/getattr(FLAGS, 'from-lang'):  'en'
# for elm in [*FLAGS]: delattr(FLAGS, elm)


def _cleanup():
    # print('')
    # print("cleaning it up...")
    try:
        LOOP.run_until_complete(BROWSER.close())
    except Exception as exc:
        logger.error(" BROWSER.close() exc: %s", exc)


def _leave_1(*args):
    print("_leave1 args:", args)
    print("from _leave1")


atexit.register(_cleanup)
# atexit.register(_leave_1, *sys.argv)


# def main(argv):
def proc_argv(argv):  # noqa
    """__main__ main."""
    del argv

    # version = "0.1.0"
    if FLAGS.version:
        print("deepl-tr-pyppeteer %s" % __version__)
        return None

    if FLAGS.debug or DEBUG:
        logzero.loglevel(10)  # logging.DEBUG
    else:
        logzero.loglevel(20)  # logging.INFO

    logger.debug("\n\t args: %s", dict((elm, getattr(FLAGS, elm)) for elm in FLAGS))

    # to_lang = FLAGS.to_lang
    # from_lang = FLAGS.from_lang

    # to_lang = getattr(FLAGS, "to-lang")
    # from_lang = getattr(FLAGS, "from-lang")
    # width = getattr(FLAGS, "width")
    # copyto = getattr(FLAGS, "copyto")
    # debug = getattr(FLAGS, "debug")

    _ = """
    args = [
        "filepath",
        "from_lang",
        "to_lang",
        "copyfrom",
        "copyto",
        "debug",
        version,
    ]
    # """

    filepath = FLAGS.filepath
    filepath = ""
    from_lang = getattr(FLAGS, "from-lang")
    to_lang = getattr(FLAGS, "to-lang")
    dualtext = FLAGS.dualtext
    output_docx = getattr(FLAGS, "output-docx")
    copyfrom = FLAGS.copyfrom
    copyto = FLAGS.copyto
    debug = FLAGS.debug or DEBUG

    # version = ""

    args = [elm.replace("-", "_") for elm in ARGS]

    logger.debug("args: %s", args)
    logger.debug("ARGS: %s", ARGS)

    _ = """  # globals wont work, if elm has been assigned values previously, globals()[args[idx]] wont work
    # still not working
    # asign args in locals()
    for idx, elm in enumerate(args):  # locals()[elm] = getattr(FLAGS, elm)
        # locals()[args[idx]] = getattr(FLAGS, elm)
        globals()[elm] = getattr(FLAGS, ARGS[idx])
        # vars()[args[idx]] = getattr(FLAGS, elm)
    # """

    for elm in args:
        logger.debug("%s, %s", elm, vars().get(elm))
        # logger.debug("%s, %s", elm, globals().get(elm))

    # logger.debug("filepath: %s", filepath)
    # raise SystemExit("exit by intention")

    # filepath, from_lang, to_lang, copyfrom, copyto, debug, version
    # available

    # if getattr(FLAGS, "debug"):
    if debug:
        logger.debug(
            "args: %s", [[elm, getattr(FLAGS, elm.replace("_", "-"))] for elm in args]
        )

    # fetch text
    text = ""
    if Path(filepath).expanduser().is_file():
        try:
            text = load_text(Path(filepath).expanduser())
        except Exception as exc:
            logger.error("load_text(%s) exc: %s", filepath, exc)
            raise SystemExit("\n\t Unable to proceed, sorry man.")
    else:
        logger.info(
            "Filepath not provided or not a file, attemptting to fetch text from system clipboard"
        )

        # browse for a file if FLAGS.copyfrom not set

        # fetch text from clipboard if copyfrom set and filepath not set
        if copyfrom:
            filepath = "clipboard.txt"
            text = pyperclip.paste()
            logger.debug("text from clipboard: %s...", text[:20])
            if not text.strip():
                logger.info(
                    " There appears to be nothing in the clipboard.\n\tGoodbye!"
                )
        else:  # browse
            filepath = browse_filename()
            if not filepath:
                logger.debug("filepath [%s]", filepath)
                logger.info("Cancelled or invalid file selected, no more option left but to exit.")

        # text = " ".join(argv[1:])
        # logger.debug("argv from terminal: %s", text)

    try:
        text = text.strip()
    except Exception as exc:
        logger.warning("text.strip() exc: %s, exiting...", exc)
        # text = ""
        return None

    # translate to to_lang via deepl
    # clean up
    text = "\n".join(
        [re.sub(r"[ ]+", " ", elm).strip() for elm in text.splitlines() if elm.strip()]
    )

    try:
        _ = deepl_tr_pp(text, from_lang, to_lang, debug)
        trtext = LOOP.run_until_complete(_)
    except Exception as exc:
        logger.error("deepl_tr_pp exc: %s", exc)
        logger.error("Unable to translate, exiting")
        raise SystemExit(1)

    lines1 = text.splitlines()
    lines2 = trtext.splitlines()

    _ = len(lines1)
    _t1 = len(lines2)
    if not _ == _t1:
        logger.warning(
            "There may be a problem, numbers of praras do not match: %s != %s", _, _t1
        )
        logger.info("We proceed anywa.")

    pairs = [*zip_longest(lines1, lines2, fillvalue="")]
    text1, text2 = [*zip(*pairs)]

    if dualtext:
        outtext = "\n".join(["\n".join(elm) for elm in pairs])
        # remove blank lines
        _ = outtext.splitlines()
        outtext = "\n".join(elm.strip() for elm in _ if elm.strip())
    else:
        outtext = "\n".join(text2)

    document = Document()
    if output_docx:
        tgt = [str(elm) for elm in text2]
        if dualtext:
            src = [str(elm) for elm in text1]
            document = gen_docx(src, tgt)
        else:
            document = gen_docx1(tgt)

    fpath = Path(filepath).expanduser().resolve()
    if output_docx:
        ofile = fpath.parent / f"{fpath.stem}-tr.docx"
        try:
            document.save(ofile)
            logger.info(" File written to %s", ofile)
        except Exception as exc:
            logger.error(" Failed to write %s, exc: %s", ofile, exc)
    else:
        ofile = fpath.parent / f"{fpath.stem}-tr.txt"
        try:
            ofile.write_text(outtext, "utf-8")
            logger.info(" File written to %s", ofile)
        except Exception as exc:
            logger.error(" Failed to write %s, exc: %s", ofile, exc)

    logger.info("\n\ttranslated to %s from %s", to_lang, from_lang)

    if copyto:
        try:
            pyperclip.copy(outtext)
            logger.info("Also copied to clipbaord")
        except Exception as exc:
            logger.error("Unable to copy, exc: %s", exc)

    return None


def main():  # noqa: F811
    """main."""
    app.run(proc_argv)


if __name__ == "__main__":
    # app.run(main)
    main()
