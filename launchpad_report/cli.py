import argparse
import os

from launchpad_report.report import Report

def main():
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
        '-o', '--output', dest='output', action='store', type=str,
        help='where to output templating result', default='report.html'
    )
    params, other_params = parser.parse_known_args()

    report = Report(
        config_filename=params.config,
        template_filename=params.template
    )

    report.generate()

    if params.output == '-':
        print report.render()
    else:
        report.render2file(params.output)
