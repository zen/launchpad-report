from __future__ import print_function

import json

from launchpadlib.launchpad import Launchpad
import yaml

from launchpad_report.checks import Checks
from launchpad_report.render import CSVRenderer
from launchpad_report.render import HTMLRenderer
from launchpad_report.render import JSONRenderer
from launchpad_report.utils import printn

all_bug_statuses = [
    'New', 'Incomplete', 'Opinion', 'Invalid', 'Won\'t Fix',
    'Expired', 'Confirmed', 'Triaged', 'In Progress',
    'Fix Committed', 'Fix Released', 'Incomplete (with response)',
    'Incomplete (without response)'
]


def is_series(obj):
    return (
        obj.resource_type_link ==
        u'https://api.launchpad.net/devel/#project_series'
    )


class ConfigError(Exception):
    pass


class Report(object):
    def __init__(self, config_filename):
        with open(config_filename, "r") as f:
            self.config = yaml.load(f.read())

        self.teams = self.config['teams']
        self.trunc = self.config['trunc_report']

        cache_dir = self.config['cache_dir']

        if self.config['use_auth']:
            lp = Launchpad.login_with(
                'lp-report-bot', 'production',
                cache_dir, version='devel'
            )
        else:
            lp = Launchpad.login_anonymously(
                'lp-report-bot', 'production', version='devel'
            )
        self.project = lp.projects[self.config['project']]
        self.blueprint_series = {}

    def render2html(self, filename, template_filename):
        HTMLRenderer(filename, template_filename).render(self.data)

    def render2csv(self, filename):
        CSVRenderer(filename).render(self.data)

    def render2json(self, filename):
        JSONRenderer(filename).render(self.data)

    def load(self, filename):
        jsonfile = open(filename)
        self.data = json.load(jsonfile)

    def generate(self):
        if self.project is None:
            raise ConfigError("No such project '%s'" % self.config['project'])
        self.checks = Checks(self.iter_series())
        self.data = {'rows': []}
        self.data['config'] = self.config
        self.bug_issues = {}
        self.data['rows'] += self.bp_report()
        self.data['rows'] += self.bug_report()

    def iter_series(self):
        print("Collecting series data:")
        self.bps_series = {}
        self.milestones_series = {}
        for series in self.project.series:
            printn(" %s" % series.name)
            # Blueprints
            for (counter, bp) in enumerate(series.all_specifications):
                self.bps_series.setdefault(bp.name, [])
                self.bps_series[bp.name].append(series.name)
            # Milestones
            for milestone in series.all_milestones:
                self.milestones_series[milestone.name] = series.name
        printn(" none")
        # Search for blueprints without series
        for (counter, bp) in enumerate(self.project.all_specifications):
            self.bps_series.setdefault(bp.name, [None])
        print()
        return {
            'milestones': self.milestones_series,
        }

    def bp_report(self):
        report = []
        blueprints = self.project.all_specifications
        printn("Processing blueprints (%d):" % len(blueprints))
        for (counter, bp) in enumerate(blueprints, 1):
            if counter > self.trunc and self.trunc > 0:
                break
            if counter % 200 == 10:
                print()
            if counter % 10 == 0:
                printn("%4d" % counter)
            assignee = 'unassigned'
            assignee_name = 'unassigned'
            try:
                assignee = bp.assignee.name
                assignee_name = bp.assignee.display_name
            except Exception:
                pass
            if bp.milestone:
                milestone = bp.milestone.name
            else:
                milestone = 'None'
            team = 'unknown'
            status = 'error'
            for t in self.teams.keys():
                if assignee in self.teams[t]:
                    team = t
            if bp.is_started and not bp.is_complete:
                status = 'in progress'
            if not bp.is_started and not bp.is_complete:
                status = 'backlog'
            if bp.is_complete:
                status = 'done'
            triage = self.checks.run(bp, self.bps_series[bp.name])
            report.append({
                'type': 'bp',
                'link': bp.web_link.encode('utf-8'),
                'id': bp.web_link[
                    bp.web_link.rfind('/') + 1:
                ].encode('utf-8'),
                'title': bp.title.encode('utf-8'),
                'milestone': milestone,
                'series': self.bps_series[bp.name],
                'status': bp.implementation_status,
                'short_status': status,
                'priority': bp.priority,
                'team': team.encode('utf-8'),
                'assignee': assignee.encode('utf-8'),
                'name': assignee_name.encode('utf-8'),
                'triage': ', '.join(triage).encode('utf-8')
            })
        print()
        return report

    def bug_report(self):
        report = []
        bugs = self.project.searchTasks(status=all_bug_statuses)
        printn("Processing bugs (%d):" % len(bugs))

        for (counter, bug) in enumerate(bugs, 1):
            if counter > self.trunc and self.trunc > 0:
                break
            if counter % 200 == 10:
                print()
            if counter % 10 == 0:
                printn("%4d" % counter)
            assignee = 'unassigned'
            assignee_name = 'unassigned'
            try:
                assignee = bug.assignee.name
                assignee_name = bug.assignee.display_name
            except Exception:
                pass
            if bug.milestone:
                milestone = bug.milestone.name
            else:
                milestone = 'None'
            team = 'unknown'
            status = 'backlog'
            self.bug_issues.setdefault(bug.bug.web_link, [])
            for t in self.teams.keys():
                if assignee in self.teams[t]:
                    team = t
            title = bug.bug.title
            if bug.is_complete:
                status = 'done'
            if (
                bug.status == 'Fix Committed' or
                bug.status == 'Fix Released' or
                bug.status == 'Incomplete'
            ):
                status = 'done'
            if bug.status == 'In Progress':
                status = 'in progress'
            triage = []
            for task in bug.bug.bug_tasks:
                series = task.target
                if is_series(series):
                    series = series.name
                else:
                    series = None
                triage += self.checks.run(task, series)
            report.append({
                'type': 'bug',
                'link': bug.web_link.encode('utf-8'),
                'id': bug.web_link[
                    bug.web_link.rfind('/') + 1:
                ].encode('utf-8'),
                'title': title.encode('utf-8'),
                'milestone': milestone,
                'status': bug.status,
                'short_status': status,
                'priority': bug.importance,
                'team': team.encode('utf-8'),
                'assignee': assignee.encode('utf-8'),
                'name': assignee_name.encode('utf-8'),
                'triage': ', '.join(triage).encode('utf-8'),
            })
        print()
        return report
