Originally: pmon - Process Monitor
Copyright 2014 Matthew Wall
Source at doc/weewx/examples/pmon
https://github.com/weewx/weewx/tree/master/examples/pmon
#
Now: pmon+ - Process Monitor+
Modified and renamed 2018 by Glenn McKechnie
Database changes require a renaming to prevent clashes.
https://github.com/glennmckechnie/weewx-pmonplus
#

Introduction for pmon (from the original notes)
This example illustrates how to implement a service and package it so that it
can be installed by the extension installer.  The pmon service collects memory
usage information about a single process then saves it in its own database.
Data are then displayed using standard weewx reporting and plotting utilities.

Changes for pmon+
The pmon+ (2018) modifications increases the fields that are captured.

    ('mem_vsz', 'INTEGER'),
    ('mem_rss', 'INTEGER'),
    ('res_rss', 'INTEGER'),
    ('swap_total', 'INTEGER'),
    ('swap_free', 'INTEGER'),
    ('swap_used', 'INTEGER'),
    ('mem_total', 'INTEGER'),
    ('mem_free', 'INTEGER'),
    ('mem_used', 'INTEGER'),

mem_vsz and mem_rss are as per the original pmon except they are
identified by the process PID rather than the process name (weewxd)
This enables pmon+ to be run with multiple instances of weewx running on
the same machine.

res_rss is max rss as returned from the python resource module. (which
can be inserted into the python (weewx) scripts for troubleshooting)

swap_total, swap_free, swap_used are values returned by cat /proc/meminfo

mem_total, mem_free, mem_used are also values returned by cat /proc/meminfo

Not all values are plotted by default. User choice decides.



Installation instructions:
1. download the package:
wget -O weewx-pmon+.zip https://github.com/glennmckechnie/weewx-pmonplus/archive/master.zip


1) run the installer:
use the package name (master.zip)

wee_extension --install weewx-pmon+.zip
2) restart weewx:

sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start


This will result in a skin called pmon+ with a single web page that illustrates
how to use the monitoring data.  See comments in pmon+.py for customization
options, also review the original doc/weewx/examples/pmon


pmon+

Entries added to weewx.conf

units : database entries will be modified using this value - before storing
        use with caution as once applied the values are (semi-)permanent
        (they will dissappear after the max+_age has elapsed.)
max_age : time after which database values will be deleted (see above).

# Options for extension 'pmon+'
[ProcessMonitor+]
    data_binding = pmon+_binding
    #max_age = 1209600 # delete records after 14 days (default 30 days)
    #units = 1048576 # GB for y scale images (default 1024 - MB)

The main changes to the original pmon are as follows...

0.5.3 March 2018
* modifications to mwalls existing pmon by Glenn McKechie
 https://github.com/glennmckechnie
* renamed to pmon+ purely to prevent clashes with the existing pmon
 extension. The databases are incompatable.
* change process selection (weewxd) to use os.getpid() (PID) to enable usage
 with multiple weewx instances. Run this extension within each weewx instance
 , change the HTML_ROOT = /var/www/html/weewx/pmon entry in the [stdReport]
 section of weewx.conf to seperate report output.
* removed process = weewxd from weewx.conf. pmon+ will only ever track weewxd,
 - see point directly above. There is no longer an option to change it so
 removal is to prevent possible confusion. If you wish to track other
 process's use the original pmon.
* modify code to use swap and mem values from /proc/meminfo,
 Code used was sourced from the cmon extension by mwall.
* add res_rss column to database to allow storage of python-resource max rss
 values for comparison to original mem_* values or debugging values, if the
 user includes such code elsewhere?
* option to store values in the database as MB (this is a workaround to
 fix the image labelling for y axis when there are too many zeros - think GBs)
* database changed to floating point to allow expression of smaller values (KB).
* display $latest.tag-value as weewx tags for inclusion in index.html.tmpl
* reworked __main__ to run as stand alone.

See changelog.txt in the tarball for all changes.

