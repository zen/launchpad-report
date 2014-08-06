import argparse
from launchpad_report.report import Report
import logging
import os
import sys

import httplib
import traceback


logger = logging.getLogger(__name__)


# All this http-related code is an attempt to cache duplicated requests
# Right now it just finds all duplicated requests and send traceback.

my_cache = {}


def my_request(*args, **kwargs):
    # self = args[0]
    method = args[1]
    url = args[2]
    if method == 'GET':
        if url in my_cache:
            logger.debug("Hit " + url)
            logger.debug(''.join(traceback.format_stack()))
            # return
        else:
            logger.debug("Miss " + url)
            my_cache[url] = 1
            # self.my_url = url
            # self.my_method = method
    return old_httplib_request(*args, **kwargs)


class my_resp_obj(dict):
    def __init__(self, obj):
        self.status = obj.status
        self.reason = obj.reason
        self.data = obj.read()
        self.headers = obj.getheaders()

    def read(self):
        return self.data

    def getheaders(self):
        return self.headers


def my_response(*args, **kwargs):
    self = args[0]
    method = self.my_method
    url = self.my_url
    if (
        method == 'GET' and
        (url.startswith('/devel/~') or url.startswith('/devel/fuel'))
    ):
        if url in my_cache:
            logger.debug("Hit " + url)
        else:
            logger.debug("Miss " + url)
            my_cache[url] = 1
                # my_resp_obj(old_httplib_response(*args, **kwargs))
        # return my_cache[url]
    # return old_httplib_response(*args, **kwargs)

old_httplib_request = httplib.HTTPConnection.request
httplib.HTTPConnection.request = my_request
#old_httplib_response = httplib.HTTPConnection.getresponse
#httplib.HTTPConnection.getresponse = my_response

# /http_magic


def main():
    reload(sys)
    sys.setdefaultencoding('utf-8')
    description = """
    Generate status report for bugs and blueprints in Launchpad project
    """
    parser = argparse.ArgumentParser(epilog=description)
    parser.add_argument(
        '--template', dest='template', action='store', type=str,
        help='html template file',
        default=os.path.join(os.path.dirname(__file__), 'template.html')
    )
    parser.add_argument(
        '-c', '--config', dest='config', action='store', type=str,
        help='yaml config file',
        default=os.path.join(os.path.dirname(__file__), 'config.yaml')
    )
    parser.add_argument(
        '--outjson', dest='outjson', action='store', type=str,
        help='where to output json report', default='report.json'
    )
    parser.add_argument(
        '--outcsv', dest='outcsv', action='store', type=str,
        help='where to output csv report', default='report.csv'
    )
    parser.add_argument(
        '--outhtml', dest='outhtml', action='store', type=str,
        help='where to output html report', default='report.html'
    )
    parser.add_argument(
        '--load-json', dest='loadjson', action='store', type=str,
        help='generate report from previous json report'
    )
    parser.add_argument(
        '-l', '--logfile', dest='logfile', action='store', type=str,
        help='Generate debug logfile'
    )
    params, other_params = parser.parse_known_args()

    report = Report(
        config_filename=params.config
    )

    if params.logfile:
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(params.logfile)
        logger.addHandler(file_handler)
    else:
        logger.setLevel(logging.WARNING)

    if params.loadjson:
        report.load(params.loadjson)
    else:
        report.generate()

    report.render2csv(params.outcsv)
    report.render2json(params.outjson)
    report.render2html(params.outhtml, params.template)
