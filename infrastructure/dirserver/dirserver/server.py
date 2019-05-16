from flask import Flask

APP = Flask(__name__)


@APP.route('/')
def index():
    return "MLS DIR SERVER"


def main():
    APP.run(host='0.0.0.0')


if __name__ == '__main__':
    main()
