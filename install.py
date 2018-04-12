# installer for pmon+ (was pmon)
# Copyright 2014 Matthew Wall
# modified 2018 by glenn mckechnie

from setup import ExtensionInstaller

def loader():
    return ProcessMonitorInstaller()

class ProcessMonitorInstaller(ExtensionInstaller):
    def __init__(self):
        super(ProcessMonitorInstaller, self).__init__(
            version="0.5.3",
            name='pmon+',
            description='Collect and display the memory usage of the weewx process.',
            author="Matthew Wall, modified by Glenn McKechnie",
            author_email="<mwall@users.sourceforge.net>, <glenn.mckechnie@gmail.com>",
            process_services='user.pmon+.ProcessMonitor',
            config={
                'ProcessMonitor+': {
                    'data_binding': 'pmon+_binding'},
                'DataBindings': {
                    'pmon+_binding': {
                        'database': 'pmon+_sqlite',
                        'table_name': 'archive',
                        'manager': 'weewx.manager.DaySummaryManager',
                        'schema': 'user.pmon+.schema'}},
                'Databases': {
                    'pmon+_sqlite': {
                        'database_name': 'pmon+.sdb',
                        'driver': 'weedb.sqlite'}},
                'StdReport': {
                    'pmon+': {
                        'skin': 'pmon+',
                        'HTML_ROOT': 'pmon+'}}},
            files=[('bin/user', ['bin/user/pmon+.py']),
                   ('skins/pmon+', ['skins/pmon+/skin.conf',
                                    'skins/pmon+/index.html.tmpl'])]
            )
