import argparse
import os
import sys

from launchpad_report.report import Report


def main():
    reload(sys)
    sys.setdefaultencoding('utf-8')
    description = """
    Generate status report for bugs and blueprints in Launchpad project
    """
    parser = argparse.ArgumentParser(epilog=description)
    parser.add_argument(
        '-t', '--template', dest='template', action='store', type=str,
        help='html template file',
        default=os.path.join(os.path.dirname(__file__), 'template.html')
    )
    parser.add_argument(
        '-c', '--config', dest='config', action='store', type=str,
        help='yaml config file',
        default=os.path.join(os.path.dirname(__file__), 'config.yaml')
    )
    parser.add_argument(
        '-j', '--outjson', dest='outjson', action='store', type=str,
        help='where to output json report', default='report.json'
    )
    parser.add_argument(
        '-c', '--outcsv', dest='outcsv', action='store', type=str,
        help='where to output csv report', default='report.csv'
    )
    parser.add_argument(
        '-t', '--outhtml', dest='outhtml', action='store', type=str,
        help='where to output html report', default='report.html'
    )
    parser.add_argument(
        '-l', '--load-json', dest='loadjson', action='store', type=str,
        help='generate report from previous json report'
    )
    params, other_params = parser.parse_known_args()

    report = Report(
        config_filename=params.config,
        template_filename=params.template
    )

    if params.loadjson:
        report.load(params.loadjson)
    else:
        report.generate()

    # if params.output == '-':
    #     print report.render()
    # else:
    report.render2csv(params.outcsv)
    report.render2json(params.outjson)
    report.render2html(params.outhtml)
