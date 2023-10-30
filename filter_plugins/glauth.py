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
            'checksum': self.checksum,
            'glauth_plugins': self.plugins,
            'support_tls': self.support_tls,
            'tls_directory': self.tls_directory,
            'combine_lists': self.combine_lists
        }

    def release_version(self, data, artefact, version, os, arch):
        """
        """
        # display.v(f"release_version(self, data, {artefact}, {version}, {os}, {arch})")
        download_url = None
        urls = []
        # display.v(f"  {type(data)}")
        if isinstance(data, list):
            """
            """
            for d in data:
                """
                """
                assets = d.get("assets", [])

                if assets and len(assets) > 0:
                    for url in assets:
                        urls.append(url.get("browser_download_url"))

        display.v(f" - {urls}")

        # https://github.com/glauth/glauth/releases/download/v2.2.0-RC1/glauth-linux-amd64
        # https://github.com/glauth/glauth/releases/download/v2.1.0/darwinamd64.zip'
        download_url = [x for x in urls if re.search(rf".*{version}.*{os}.*{arch}.*", x)][0]

        display.v(f"= download_url: {download_url}")

        return download_url

    def checksum(self, data, artefact, os, arch):
        """
        """
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
        # display.v("plugins(self, data")

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
        display.v(f"support_tls({data})")

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
        display.v(f"tls_directory({data})")

        directory = []

        cert_file = data.get("tls", {}).get("cert_file", None)
        key_file = data.get("tls", {}).get("key_file", None)

        if cert_file and key_file:
            directory.append(os.path.dirname(cert_file))
            directory.append(os.path.dirname(key_file))

        directory = list(set(directory))

        if len(directory) == 1:
            return directory[0]

    def combine_lists(self, data, second):
        """
            This keeps only unique name in the list, not preserving the order though.
        """
        display.v(f"combine_lists({data}, {second})")

        result = list({x['name']: x for x in data + second}.values())

        display.v(f"= {result}")

        return result
