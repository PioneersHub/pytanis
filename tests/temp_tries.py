import json

from src.pytanis.pretalx.models import Submission

submission = json.load(open('/Users/hendorf/code/pioneershub/py_tube/src/_tmp/pretalx/3CYZUH.json'))
b = Submission(**submission)

a = 44
