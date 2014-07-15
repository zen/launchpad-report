import yaml
import os

from launchpadlib.launchpad import Launchpad

from launchpad_report.utils import printn, UnicodeWriter

config = yaml.load(open(
    os.path.join(os.path.dirname(__file__), 'config.yaml'),
    'r'
))
PROJECT = config['project']
CURRENT_MILESTONE = str(config['current_milestone'])
teams = config['teams']
REPORT_FILE = config['report_file']
LIMIT_COUNT = config['trunc_report']

lp = Launchpad.login_anonymously(
    'launchpad-report-bot', 'production', version='devel'
)
project = lp.projects[PROJECT]
current_series = project.getMilestone(name=CURRENT_MILESTONE).series_target
blueprint_series = {}


def check_bp(bp):
    issues = []
    if bp.priority == 'Undefined':
        issues.append('No priority')
    if bp.priority == 'Not':
        issues.append('Not priority')
    if not bp.assignee:
        issues.append('No assignee')
    if not bp.milestone:
        issues.append('No milestone')
    if not bp.web_link in blueprint_series.keys():
        issues.append('No series')
    else:
        series = project.getSeries(name=blueprint_series[bp.web_link])
        if bp.milestone not in series.active_milestones:
            issues.append('Wrong milestone')
    return issues


def check_bug(bug):
    issues = []
    if bug.importance == 'Undecided':
        issues.append('No priority')
    if not bug.assignee:
        issues.append('No assignee')
    if not bug.milestone:
        issues.append('No milestone')
    if bug.status == 'New':
        issues.append('Not triaged')
    if bug.milestone.name != CURRENT_MILESTONE:
        issues.append('Not related to current milestone')
    return issues


# Launchpad API does not allow to get series of a blueprint
def calc_bp_series():
    print("Collecting blueprint series:")
    for series in project.series:
        printn(" %s" % series.name)
        for (counter, bp) in enumerate(series.valid_specifications):
            if counter > LIMIT_COUNT and LIMIT_COUNT > 0:
                break
            blueprint_series[bp.web_link] = series.name
    print


def bp_report(reporter):
    blueprints = project.valid_specifications
    print("Processing blueprints (%d):" % len(blueprints))
    for (counter, bp) in enumerate(blueprints, 1):
        if counter > LIMIT_COUNT and LIMIT_COUNT > 0:
            break
        if counter % 10 == 0:
            printn("%4d" % counter)
        if counter % 200 == 0:
            print
        assignee = 'unassigned'
        assignee_name = 'unassigned'
        try:
            assignee = bp.assignee.name
            assignee_name = bp.assignee.display_name
        except:
            pass
        team = 'unknown'
        status = 'error'
        for t in teams.keys():
            if assignee in teams[t]:
                team = t
        if bp.is_started and not bp.is_complete:
            status = 'in progress'
        if not bp.is_started and not bp.is_complete:
            status = 'backlog'
        if bp.is_complete:
            status = 'done'
        if status != 'done':
            reporter.writerow([
                'bp', bp.web_link, bp.title, bp.implementation_status,
                bp.priority, team, assignee, assignee_name,
                ', '.join(check_bp(bp))
            ])
    print

bug_issues = {}


def calc_bug_series():
    print("Processing bugs on series:")

    for series in project.series:
        printn(" %s" % series.name)
        milestones = series.active_milestones
        for (counter, task) in enumerate(series.searchTasks()):
            if counter > LIMIT_COUNT and LIMIT_COUNT > 0:
                break
            bug = task.bug
            bug_issues.setdefault(bug.web_link, [])
            if task.milestone not in milestones:
                bug_issues[bug.web_link].append(
                    "Incorrect milestone for %s" % series.name
                )
            if series == current_series:
                bug_issues[bug.web_link].append(
                    "Remove targeting to current series"
                )
            pass
    print


def bug_report(reporter):
    bugs = project.searchTasks()
    print("Processing bugs (%d):" % len(bugs))

    for (counter, bug) in enumerate(bugs, 1):
        if counter > LIMIT_COUNT and LIMIT_COUNT > 0:
            break
        if counter % 10 == 0:
            printn("%4d" % counter)
        if counter % 200 == 0:
            print
        assignee = 'unassigned'
        assignee_name = 'unassigned'
        try:
            assignee = bug.assignee.name
            assignee_name = bug.assignee.display_name
        except:
            pass
        team = 'unknown'
        status = 'backlog'
        bug_issues.setdefault(bug.bug.web_link, [])
        for t in teams.keys():
            if assignee in teams[t]:
                team = t
        title = bug.bug.title
        if bug.is_complete:
            status = 'done'
        if bug.status == 'Fix Committed' or bug.status == 'Fix Released' \
                or bug.status == 'Incomplete':
            status = 'done'
        if bug.status == 'In Progress':
            status = 'in progress'
        if status != 'done':
            reporter.writerow([
                'bug', bug.web_link, title, bug.status, bug.importance, team,
                assignee, assignee_name,
                ', '.join(check_bug(bug) + bug_issues[bug.bug.web_link]),
            ])

    print  # /bugs


def main():
    csvfile = open(REPORT_FILE, 'wb')
    reporter = UnicodeWriter(csvfile)
    reporter.writerow([
        '', 'Link', 'Title', 'Status', 'Priority', 'Team', 'Nick', 'Name',
        'Triage actions'
    ])
    calc_bp_series()
    bp_report(reporter)
    calc_bug_series()
    bug_report(reporter)
