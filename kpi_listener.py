import logging, json
from json import dumps
from enum import Enum
from typing import List
from base64 import b64encode

import locust.env
from locust.stats import calculate_response_time_percentile


class Metric(Enum):
    ERROR_RATE = 'error_rate'
    PERCENTILE_90 = 'percentile_90'
    RPS = 'rps'
    ERROR_RATE_TESTKEY = 'XT-240'
    PERCENTILE_90_TESTKEY = 'XT-241'
    RPS_TESTKEY = 'XT-242'

    @staticmethod
    def has_value(item):
        return item in [v.value for v in Metric.__members__.values()]


class KpiPlugin:
    def __init__(
            self,
            env: locust.env.Environment,
            kpis: List,
    ):
        data = {}
        data['tests'] = []
        self.data = data
        self.env = env
        self.kpis = kpis
        self.errors = []
        self._validate_kpis()

        events = self.env.events
        events.quitting.add_listener(self.quitting)  # pyre-ignore

    def quitting(self, environment):
        serialized_stats = self.serialize_stats(self.env.stats)
        updated_stats = self._update_data(serialized_stats)
        self._kpi_check(updated_stats)
        self._interpret_errors()
        self.writeToXrayResultFile()

    def serialize_stats(self, stats):
        return [stats.entries[key].serialize() for key in stats.entries.keys() if
                not (stats.entries[key].num_requests == 0 and stats.entries[key].num_failures == 0)]

    def _update_data(self, stats):
        for stat in stats:
            stat['error_rate'] = self._calculate_fail_rate(stat)
            stat['percentile_90'] = self._calculate_percentile(stat, 0.90)
            stat['rps'] = self._calculate_rps(stat)
        return stats

    def _calculate_rps(self, stat):
        rps = stat['num_reqs_per_sec']
        num_of_measurements = len(rps)
        return sum(rps.values()) / num_of_measurements

    def _calculate_fail_rate(self, stat):
        num_failures = stat['num_failures']
        num_requests = stat["num_requests"]
        return (num_failures / num_requests) * 100

    def _calculate_percentile(self, stat, percentile):
        response_times = stat['response_times']
        num_requests = stat['num_requests']
        return calculate_response_time_percentile(response_times, num_requests, percentile)

    def _kpi_check(self, stats):
        if len(stats) == 0:
            return

        for kpi in self.kpis:
            name = list(kpi.keys())[0]
            stat = next(stat for stat in stats if stat["name"] == name)
            if stat:
                kpi_settings = kpi[list(kpi.keys())[0]]
                for kpi_setting in kpi_settings:
                    self._metrics_check(kpi_setting, stat)

    def _metrics_check(self, kpi_setting, stat):
        (metric, value) = kpi_setting
        name = stat["name"]
        if metric == Metric.ERROR_RATE.value:
            error_rate = stat['error_rate']
            error_rate <= value or self._log_error(error_rate, kpi_setting, name, Metric.ERROR_RATE_TESTKEY.value)
        if metric == Metric.PERCENTILE_90.value:
            percentile = stat['percentile_90']
            percentile <= value or self._log_error(percentile, kpi_setting, name, Metric.PERCENTILE_90_TESTKEY.value)
        if metric == Metric.RPS.value:
            rps = stat['rps']
            rps >= value or self._log_error(rps, kpi_setting, name, Metric.RPS_TESTKEY.value)

    def _log_error(self, stat_value, kpi_settings, name, key):
        (metric, value) = kpi_settings
        errorlog = f"{metric} for '{name}' is {stat_value}, but expected it to be better than {value}"
        self.appendToXrayResult(key, metric, name, value, errorlog, 'FAILED')
        self.errors.append(errorlog)  # noqa: E501

    def _interpret_errors(self):
        if len(self.errors) == 0:
            logging.info('All KPIs are good!')
            self.appendToXrayResult(Metric.ERROR_RATE_TESTKEY, 'All KPIs are good!', 'PASSED')
            self.appendToXrayResult(Metric.PERCENTILE_90_TESTKEY, 'All KPIs are good!', 'PASSED')
            self.appendToXrayResult(Metric.RPS_TESTKEY, 'All KPIs are good!', 'PASSED')
        else:
            for error in self.errors:
                strMessage = f"SLA failed: \n {error}"
                logging.error(strMessage)
            self.env.process_exit_code = 1

    def _validate_kpis(self):
        for kpi in self.kpis:
            kpi_keys = list(kpi.keys())
            if len(kpi_keys) > 1:
                raise Exception("Every dict must contain definition for only one endpoint")
            kpi_settings = kpi[kpi_keys[0]]
            if len(kpi_settings) == 0:
                raise Exception(f"No KPI defined for endpoint {kpi_keys[0]}")
            for kpi_setting in kpi_settings:
                (metric, value) = kpi_setting
                if not isinstance(value, (int, float)):
                    raise Exception(f"Provide valid value for '{metric}' metric for endpoint {kpi_keys[0]}")
                if not Metric.has_value(metric):
                    raise Exception(f"Metric {metric} not implemented")

    @staticmethod
    def injectCSVFile(fileName):
        with open(fileName, 'rb') as open_file:
            byte_content = open_file.read()

        return b64encode(byte_content).decode('utf-8')

    def appendToXrayResult(self, testkey, metric, name, value,  comment, status):
        done = False
        if self.data['tests']:
            for tests in self.data['tests']:
                for key, value in tests.items():
                    if key == 'testKey' and value == testkey:
                        tests['results'].append({
                            'name': metric + ' for ' + name,
                            'log': comment,
                            'status': status
                        })
                        done = True
        
        if not done: 
            info = {
                'info': {
                    'summary': ' Perf test',
                    'description': 'Perf test',
                    'project': 'XT',
                    'testPlanKey': 'XT-239',
                },
            }
            
            self.data['tests'].append({
                'testKey': testkey,
                'comment': metric,
                'status': status,
                'results': [
                    {
                        'name': metric + ' for ' + name,
                        'log': comment,
                        'status': status
                    }
                ],
                'evidences': [
                    {
                        'data': self.injectCSVFile('example_exceptions.csv'),
                        'filename': 'performanceexceptions.csv',
                        'contentType': 'text/csv'
                    },
                    {
                        'data': self.injectCSVFile('example_failures.csv'),
                        'filename': 'performancefailures.csv',
                        'contentType': 'text/csv'
                    },
                    {   
                        'data': self.injectCSVFile('example_stats_history.csv'),
                        'filename': 'performancstatshistory.csv',
                        'contentType': 'text/csv'
                    },
                    {   
                        'data': self.injectCSVFile('example_stats.csv'),
                        'filename': 'performancstats.csv',
                        'contentType': 'text/csv'
                    }
                ]
            })

            info.update(self.data)
            self.data = info


    def writeToXrayResultFile(self):
        with open('xrayResults.json', 'w') as outfile:
            json.dump(self.data, outfile)

    


