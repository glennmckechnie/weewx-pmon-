pmon+ - Process Monitor
Copyright 2014 Matthew Wall
Modified 2018 by Glenn McKechnie at https://github.com/glennmckechnie

Introduction for pmon
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
identified by the process PID rather than the provcess name (weewxd)
This enables pmon+ to be run with multiple instances of weewx running on
the same machine.

res_rss is max rss as returned from the python resource module. (which
can be inserted into the weewx scripts for troubleshooting)

swap_total, swap_free, swap_used are values returned by cat /proc/meminfo

mem_total, mem_free, mem_used are also values returned by cat /proc/meminfo

Not all values are plotted by default. User choice decides.



Installation instructions:

1) run the installer:

wee_extension --install pmon+  # (or package name)

2) restart weewx:

sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start


This will result in a skin called pmon+ with a single web page that illustrates
how to use the monitoring data.  See comments in pmon+.py for customization
options.


pmon and pmon+

Entries added to weewx.conf

units : database entries will be modified using this value - before storing
        use with caution as once applied the values are (semi-)permanent
        (they will dissappear after the max+_age has elapsed.)
max_age : time after which database values will be deleted (see above).

# Options for extension 'pmon+'
[ProcessMonitor]
    process = weewxd
    data_binding = pmon_binding
    #max_age = 1209600 # delete records after 14 days (default 30 days)
    # The following is for pmon+ only
    #units = 1048576 # GB for y scale images (default 1024 - MB)

See changelog.txt in the tarball for details of any changes.
