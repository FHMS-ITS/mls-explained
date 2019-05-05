import re
import pytest
from pylint import epylint as lint

MIN_LINT_RATING = 10.00


def check_module_codestyle(path):
    (pylint_stdout, _) = lint.py_run(path, return_std=True)
    output = pylint_stdout.getvalue()

    assert output
    rating_match = re.search(
        r"^\s*Your code has been rated at (-?\d+(?:\.\d+))\/10",
        output,
        re.MULTILINE
    )

    if not rating_match:
        pytest.fail(
            'Could not determine rating from pylint output. Pylint output: \n%s\n' % output,
            False
        )

    rating = float(rating_match.group(1))
    if rating < MIN_LINT_RATING:
        pytest.fail('Pylint rates your code %.2f/10, which is lower than the acceptable threshold (%.2f). '
                    'Please fix your codestyle and try again.\n'
                    'Pylint output: \n%s\n' % (rating, MIN_LINT_RATING, output),
                    False
                    )


def test_module_codestyle():
    check_module_codestyle('./')
