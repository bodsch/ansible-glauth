# python 3 headers, required if submitting to Ansible

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import os
from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
      ansible filter
    """

    def filters(self):
        return {
            'release_version': self.release_version,
            # 'checksum': self.checksum,
            'glauth_plugins': self.plugins,
            'support_tls': self.support_tls,
            'tls_directory': self.tls_directory,
            'combine_lists': self.combine_lists
        }

    def release_version(self, data, version):
        """
        """
        display.v(f"glauth::release_version(data: {data}, aversion: {version})")

        _VERSION_PATTERN = re.compile(r".*\/download\/(?P<version>.*)\/.*")

        match = _VERSION_PATTERN.search(data)
        return match.group(1) if match else None

    def checksum(self, data, artefact, os, arch):
        """
        """
        display.v(f"glauth::checksum(data: {data}, artefact: {artefact}, os: {os}, arch: {arch})")

        checksum = None

        if isinstance(data, list):
            # filter OS
            # linux = [x for x in data if re.search(r".*prometheus-.*.{}.*.tar.gz".format(os), x)]
            # filter OS and ARCH
            checksum = [x for x in data if re.search(r".*{}-.*.{}-{}.tar.gz".format(artefact, os, arch), x)][0]

        if isinstance(checksum, str):
            checksum = checksum.split(" ")[0]

        # display.v("= checksum: {}".format(checksum))

        return checksum

    def plugins(self, data):
        """
        """
        display.v(f"glauth::plugins(data: {data})")

        result = []

        for d in data:
            path = d.get("path")

            if path:
                basename = os.path.basename(path)

                result.append(basename)

        return result

    def support_tls(self, data):
        """
        """
        display.v(f"glauth::support_tls(data: {data})")

        enabled = data.get("enabled", False)

        cert_file = data.get("tls", {}).get("cert_file", None)
        key_file = data.get("tls", {}).get("key_file", None)

        if enabled and cert_file and key_file:
            return True
        else:
            return False

    def tls_directory(self, data):
        """
        """
        display.v(f"glauth::tls_directory(data: {data})")

        directory = []

        cert_file = data.get("tls", {}).get("cert_file", None)
        key_file = data.get("tls", {}).get("key_file", None)

        if cert_file and key_file:
            directory.append(os.path.dirname(cert_file))
            directory.append(os.path.dirname(key_file))

        directory = list(set(directory))

        if len(directory) == 1:
            return directory[0]

    def combine_lists(self, data, configured, release_version):
        """
            This keeps only unique name in the list, not preserving the order though.
        """
        display.v(f"glauth::combine_lists(data: {data}, configured: {configured}, release_version: {release_version})")

        result = list({x['name']: x for x in data + configured}.values())

        if release_version:
            result = [
                {**p, "src": re.sub(r'v\d+\.\d+\.\d+', release_version, p["src"])}
                for p in result
            ]

        display.v(f"= {result}")

        return result
