# Copyright 2013 Matthew Wall
"""weewx module that records process information.

Installation

Put this file in the bin/user directory.


Configuration

Add the following to weewx.conf:

[ProcessMonitor]
    data_binding = pmon+_binding

[DataBindings]
    [[pmon+_binding]]
        database = pmon+_sqlite
        manager = weewx.manager.DaySummaryManager
        table_name = archive
        schema = user.pmon+.schema

[Databases]
    [[pmon+_sqlite]]
        database_name = archive/pmon+.sdb
        database_type = SQLite

[Engine]
    [[Services]]
        archive_services = ..., user.pmon+.ProcessMonitor
"""

import os
import platform
import re
import syslog
import time
from subprocess import Popen, PIPE
import resource

import weewx
import weedb
import weeutil.weeutil
from weewx.engine import StdService

VERSION = "0.5.3"

def logmsg(level, msg):
    syslog.syslog(level, 'pmon+: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)

schema = [
    ('dateTime', 'INTEGER NOT NULL PRIMARY KEY'),
    ('usUnits', 'INTEGER NOT NULL'),
    ('interval', 'INTEGER NOT NULL'),
    ('mem_vsz', 'REAL'),
    ('mem_rss', 'REAL'),
    ('res_rss', 'REAL'),
    ('swap_total', 'REAL'),
    ('swap_free', 'REAL'),
    ('swap_used', 'REAL'),
    ('mem_total', 'REAL'),
    ('mem_free', 'REAL'),
    ('mem_used', 'REAL'),
]

# add the required units and then
# add databinding stanza to [CheetahGenerator] in .conf
weewx.units.obs_group_dict['mem_vsz'] = 'group_data'
weewx.units.obs_group_dict['mem_rss'] = 'group_data'
weewx.units.obs_group_dict['res_rss'] = 'group_data'
weewx.units.obs_group_dict['swap_total'] = 'group_data'
weewx.units.obs_group_dict['swap_free'] = 'group_data'
weewx.units.obs_group_dict['swap_used'] = 'group_data'
weewx.units.obs_group_dict['mem_total'] = 'group_data'
weewx.units.obs_group_dict['mem_free'] = 'group_data'
weewx.units.obs_group_dict['mem_used'] = 'group_data'
weewx.units.USUnits['group_data'] = 'MB'
weewx.units.MetricUnits['group_data'] = 'MB'
weewx.units.default_unit_format_dict['MB'] = '%.2f'
weewx.units.default_unit_label_dict['MB'] = ' MB'
# 1 Byte = 0.000001 MB (in decimal)
weewx.units.conversionDict['MB'] = {'B': lambda x: x * 0.000001}


class ProcessMonitor(StdService):

    def __init__(self, engine, config_dict):
        super(ProcessMonitor, self).__init__(engine, config_dict)

        loginf("service version %s" % VERSION)
        d = config_dict.get('ProcessMonitor+', {})
        self.max_age = weeutil.weeutil.to_int(d.get('max_age', 2592000))
        # loginf("pmon+ max_age is %s" % self.max_age)
        self.meg = float(d.get('units', '1024'))
        # loginf("pmon+ units are %s" % self.meg)

        # get the database parameters we need to function
        binding = d.get('data_binding', 'pmon+_binding')
        self.dbm = self.engine.db_binder.get_manager(data_binding=binding,
                                                     initialize=True)

        # be sure database matches the schema we have
        dbcol = self.dbm.connection.columnsOf(self.dbm.table_name)
        dbm_dict = weewx.manager.get_manager_dict_from_config(config_dict,
                                                              binding)
        memcol = [x[0] for x in dbm_dict['schema']]
        if dbcol != memcol:
            raise Exception('pmon+ schema mismatch: %s != %s' % (dbcol, memcol))

        self.last_ts = None
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)

    def shutDown(self):
        try:
            self.dbm.close()
        except weedb.DatabaseError:
            pass

    def new_archive_record(self, event):
        """save data to database then prune old records as needed"""
        now = int(time.time() + 0.5)
        delta = now - event.record['dateTime']
        if delta > event.record['interval'] * 60:
            logdbg("Skipping record: time difference %s too big" % delta)
            return
        if self.last_ts is not None:
            self.save_data(self.get_data(now, self.last_ts))
        self.last_ts = now
        if self.max_age is not None:
            self.prune_data(now - self.max_age)

    def save_data(self, record):
        """save data to database"""
        self.dbm.addRecord(record)

    def prune_data(self, ts):
        """delete records with dateTime older than ts"""
        sql = "delete from %s where dateTime < %d" % (self.dbm.table_name, ts)
        self.dbm.getSql(sql)
        try:
            # sqlite databases need some help to stay small
            self.dbm.getSql('vacuum')
        except weedb.DatabaseError:
            pass

    COLUMNS = re.compile('[\S]+\s+[\d]+\s+[\d.]+\s+[\d.]+\s+([\d]+)\s+([\d]+)')

    def get_data(self, now_ts, last_ts):
        record = dict()
        record['dateTime'] = now_ts
        record['usUnits'] = weewx.METRIC
        record['interval'] = int((now_ts - last_ts) / 60)
        #  get_mem_data()
        try:
            self.wx_pid = str(os.getpid())
            cmd = 'ps up '+self.wx_pid
            loginf("cmd is %s" % cmd)
            p = Popen(cmd, shell=True, stdout=PIPE)
            o = p.communicate()[0]
            for line in o.split('\n'):
                #  loginf("line is %s" % line)
                if line.find(self.wx_pid) >= 0:
                    m = self.COLUMNS.search(line)
                    if m:
                        record['mem_vsz'] = (float(m.group(1))/self.meg)
                        record['mem_rss'] = (float(m.group(2))/self.meg)
        except (ValueError, IOError, KeyError), e:
            logerr('%s failed: %s' % (cmd, e))

        # now get swap data
        # ( from mwalls cmon )
        filename = '/proc/meminfo'
        try:
            mem_ = dict()
            with open(filename) as fp:
                for memline in fp:
                    #  loginf("memline is %s" % memline)
                    if memline.find(':') >= 0:
                        (n, v) = memline.split(':', 1)
                        mem_[n.strip()] = v.strip()
            if mem_:
                # returned values are in MB
                record['mem_total'] = (float(mem_['MemTotal'].split()[0])/self.meg)
                record['mem_free'] = (float(mem_['MemFree'].split()[0])/self.meg)
                record['mem_used'] = record['mem_total'] - record['mem_free']
                record['swap_total'] = (float(mem_['SwapTotal'].split()[0])/self.meg)
                record['swap_free'] = (float(mem_['SwapFree'].split()[0])/self.meg)
                record['swap_used'] = record['swap_total'] - record['swap_free']
        except Exception, e:
            logdbg("read failed for %s: %s" % (filename, e))

        record['res_rss'] = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/self.meg

        return record


# what follows is a basic unit test of this module.  to run the test:
#
# For Debian or Redhat/CentOS
#
# cd /to_where/pmon+lives
#
# PYTHONPATH=/usr/share/weewx/  python pmon+.py
#
# Of note - this version uses the PID of the calling process, which will be
# your terminal, or script. It will not be weewxd itself.
# The test still works to catch coding errors though!
#
if __name__ == "__main__":
    from weewx.engine import StdEngine
    config = {
        'Station': {
            'station_type': 'Simulator',
            'altitude': [0, 'foot'],
            'latitude': 0,
            'longitude': 0},
        'Simulator': {
            'driver': 'weewx.drivers.simulator',
            'mode': 'simulator'},
        'ProcessMonitor+': {
            'data_binding': 'pmon+_binding'},
        'DataBindings': {
            'pmon+_binding': {
                'database': 'pmon+_sqlite',
                'manager': 'weewx.manager.DaySummaryManager',
                'table_name': 'archive',
                'schema': 'user.pmon+.schema'}},
        'Databases': {
            'pmon+_sqlite': {
                'database_name': 'pmon+.sdb',
                'database_type': 'SQLite'}},
        'DatabaseTypes': {
            'SQLite': {
                'driver': 'weedb.sqlite',
                'SQLITE_ROOT': '/var/tmp'}},
        'Engine': {
            'Services': {
                'process_services': 'user.pmon+.ProcessMonitor'}}}
    eng = StdEngine(config)
    svc = ProcessMonitor(eng, config)

    wx_pid = str(os.getpid())
    print("process PID is %s" % wx_pid)
    nowts = lastts = int(time.time())
    rec = svc.get_data(nowts, lastts)
    print rec

    time.sleep(5)
    print("process PID is %s" % wx_pid)
    nowts = int(time.time())
    rec = svc.get_data(nowts, lastts)
    print rec

    time.sleep(5)
    print("process PID is %s" % wx_pid)
    lastts = nowts
    nowts = int(time.time())
    rec = svc.get_data(nowts, lastts)
    print rec

    os.remove('/var/tmp/pmon+.sdb')
    print "removed %s" % '/var/tmp/pmon+.sdb'
