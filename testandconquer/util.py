import textwrap
from datetime import datetime

from testandconquer import logger


def system_exit(title, body, args, exit_fn=lambda: exec('raise SystemExit')):
    args['Timestamp'] = datetime.utcnow().isoformat()
    meta = ['[{} = {}]'.format(key, val) for (key, val) in args.items()]

    text = """

{top}

[ERROR] [CONQUER] {title}

{body}

{meta}

{bottom}

""".format(top='=' * 80, title=title, body=body, meta='\n'.join(meta), bottom='=' * 80)
    text = textwrap.indent(text, '    ')
    logger.error(text)
    exit_fn()
