# coding: utf-8
from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------

# _facts = local_facts(host=host, fact="glauth")


@pytest.mark.parametrize("dirs", [
    "/etc/glauth",
    "/var/lib/glauth",
    "/usr/local/opt/glauth",
])
def test_directories(host, dirs):
    d = host.file(dirs)
    assert d.is_directory
    assert d.exists


def test_files(host, get_vars):
    """
    """
    distribution = host.system_info.distribution
    release = host.system_info.release

    print(f"distribution: {distribution}")
    print(f"release     : {release}")

    version = local_facts(host=host, fact="glauth").get("version")

    install_dir = get_vars.get("glauth_install_path")
    defaults_dir = get_vars.get("glauth_defaults_directory")
    config_dir = get_vars.get("glauth_config_dir")

    if 'latest' in install_dir:
        install_dir = install_dir.replace('latest', version)

    files = []
    files.append("/usr/bin/glauth")

    if install_dir:
        files.append(f"{install_dir}/glauth")
    if defaults_dir and not distribution == "artix":
        files.append(f"{defaults_dir}/glauth")
    if config_dir:
        files.append(f"{config_dir}/glauth.conf")

    print(files)

    for _file in files:
        f = host.file(_file)
        assert f.is_file


def test_certificates(host, get_vars):
    """
    """
    source = get_vars.get("glauth_tls_certificate").get("source_files")
    tls = get_vars.get("glauth_config").get("ldaps").get("tls")
    files = []
    files.append(source.get("cert"))
    files.append(source.get("key"))
    files.append(tls.get("cert_file"))
    files.append(tls.get("key_file"))

    for _file in files:
        f = host.file(_file)
        assert f.is_file


def test_user(host, get_vars):
    """
    """
    user = get_vars.get("glauth_system_user", "glauth")
    group = get_vars.get("glauth_system_group", "glauth")

    assert host.group(group).exists
    assert host.user(user).exists
    assert group in host.user(user).groups
    assert host.user(user).home == "/nonexistent"


def test_service(host):
    service = host.service("glauth")
    print(service)
    assert service.is_running
    assert service.is_enabled


def test_open_port(host):
    """
    """
    service = host.socket("tcp://0.0.0.0:389")
    assert service.is_listening

    service = host.socket("tcp://0.0.0.0:636")
    assert service.is_listening
