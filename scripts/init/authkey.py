#!/usr/bin/env python
import crm_script
import os
import stat

host = crm_script.host()
others = crm_script.output(1).keys()
others.remove(host)

COROSYNC_AUTH = '/etc/corosync/authkey'
COROSYNC_CONF = '/etc/corosync/corosync.conf'


def make_opts():
    from psshlib import api as pssh
    opts = pssh.Options()
    opts.timeout = 60
    opts.recursive = True
    opts.user = 'root'
    opts.ssh_options += ['PasswordAuthentication=no',
                         'StrictHostKeyChecking=no',
                         'ControlPersist=no']
    return opts


def check_results(pssh, results):
    failures = []
    for host, result in results.items():
        if isinstance(result, pssh.Error):
            failures.add("%s: %s" % (host, str(result)))
    if failures:
        crm_script.exit_fail(', '.join(failures))


def gen_authkey():
    if not os.path.isfile(COROSYNC_AUTH):
        rc, out, err = crm_script.sudo_call(['corosync-keygen', '-l'])
        if rc != 0:
            crm_script.exit_fail("Error generating key: %s" % (err))
    elif stat.S_IMODE(os.stat(COROSYNC_AUTH)[stat.ST_MODE]) != stat.S_IRUSR:
        os.chmod(COROSYNC_AUTH, stat.S_IRUSR)


def run_copy():
    try:
        from psshlib import api as pssh
    except ImportError:
        crm_script.exit_fail("Command node needs pssh installed")
    opts = make_opts()
    results = pssh.copy(others, COROSYNC_AUTH, COROSYNC_AUTH, opts)
    check_results(pssh, results)
    results = pssh.call(others,
                        "chown root:root %s;chmod 400 %s" % (COROSYNC_AUTH, COROSYNC_AUTH),
                        opts)
    check_results(pssh, results)


if __name__ == "__main__":
    gen_authkey()
    if others:
        run_copy()
