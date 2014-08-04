from __future__ import print_function

import json

from launchpadlib.launchpad import Launchpad
import yaml

from launchpad_report.render import CSVRenderer
from launchpad_report.render import HTMLRenderer
from launchpad_report.render import JSONRenderer
from launchpad_report.utils import printn


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
        self.current_milestone = self.project.getMilestone(
            name=self.config['current_milestone']
        )
        self.current_series = self.current_milestone.series_target
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
        if self.current_milestone is None:
            raise ConfigError(
                "current_milestone '%s' is incorrect" %
                self.config['current_milestone']
            )
        if self.current_series is None:
            raise ConfigError(
                "No series for '%s' milestone" %
                self.config['current_milestone']
            )
        self.data = {'rows': []}
        self.data['headers'] = [
            '', 'Link', 'Title', 'Status', 'Priority', 'Team', 'Nick', 'Name',
            'Triage actions'
        ]
        self.data['config'] = self.config
        self.bug_issues = {}
        self.calc_bp_series()
        self.data['rows'] += self.bp_report()
        self.calc_bug_series()
        self.data['rows'] += self.bug_report()

    def check_bp(self, bp):
        issues = []
        if bp.priority == 'Undefined':
            issues.append('No priority')
        if bp.priority == 'Not':
            issues.append('Not priority')
        if not bp.assignee:
            issues.append('No assignee')
        if not bp.milestone:
            issues.append('No milestone')
        if bp.web_link not in self.blueprint_series.keys():
            issues.append('No series')
        else:
            series = self.project.getSeries(
                name=self.blueprint_series[bp.web_link])
            if bp.milestone not in series.active_milestones:
                issues.append('Wrong milestone (%s)' % bp.milestone.name)
        return issues

    def check_bug(self, bug):
        issues = []
        if bug.importance == 'Undecided':
            issues.append('No priority')
        if not bug.assignee:
            issues.append('No assignee')
        if not bug.milestone:
            issues.append('No milestone')
        else:
            if bug.milestone.name != self.config['current_milestone']:
                issues.append(
                    'Related to non-current milestone (%s)' %
                    bug.milestone.name)
        if bug.status == 'New':
            issues.append('Not triaged')
        return issues

    # Launchpad API does not allow to get series of a blueprint
    def calc_bp_series(self):
        print("Collecting blueprint series:")
        for series in self.project.series:
            printn(" %s" % series.name)
            for (counter, bp) in enumerate(series.valid_specifications):
                if counter > self.trunc and self.trunc > 0:
                    break
                self.blueprint_series[bp.web_link] = series.name
        print()

    def bp_report(self):
        report = []
        blueprints = self.project.valid_specifications
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
            report.append({
                'type': 'bp',
                'link': bp.web_link.encode('utf-8'),
                'id': bp.web_link[
                    bp.web_link.rfind('/') + 1:
                ].encode('utf-8'),
                'title': bp.title.encode('utf-8'),
                'status': bp.implementation_status,
                'short_status': status,
                'priority': bp.priority,
                'team': team.encode('utf-8'),
                'assignee': assignee.encode('utf-8'),
                'name': assignee_name.encode('utf-8'),
                'triage': ', '.join(self.check_bp(bp)).encode('utf-8')
            })
        print()
        return report

    def calc_bug_series(self):
        print("Processing bugs on series:")

        for series in self.project.series:
            printn(" %s" % series.name)
            milestones = series.active_milestones
            for (counter, task) in enumerate(series.searchTasks()):
                if counter > self.trunc and self.trunc > 0:
                    break
                bug = task.bug
                self.bug_issues.setdefault(bug.web_link, [])
                if task.milestone not in milestones:
                    try:
                        milestone_name = task.milestone.name
                    except Exception:
                        milestone_name = None
                    self.bug_issues[bug.web_link].append(
                        "Incorrect milestone (%s) for %s" % (
                            milestone_name, series.name
                        )
                    )
                if series == self.current_series:
                    self.bug_issues[bug.web_link].append(
                        "Remove targeting to current series"
                    )
                pass
        print()

    def bug_report(self):
        report = []
        bugs = self.project.searchTasks()
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
            report.append({
                'type': 'bug',
                'link': bug.web_link.encode('utf-8'),
                'id': bug.web_link[
                    bug.web_link.rfind('/') + 1:
                ].encode('utf-8'),
                'title': title.encode('utf-8'),
                'status': bug.status,
                'short_status': status,
                'priority': bug.importance,
                'team': team.encode('utf-8'),
                'assignee': assignee.encode('utf-8'),
                'name': assignee_name.encode('utf-8'),
                'triage': ', '.join(
                    self.check_bug(bug) +
                    self.bug_issues[bug.bug.web_link]
                ).encode('utf-8'),
            })
        print()
        return report
