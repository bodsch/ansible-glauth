#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2023, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, print_function
import shutil
import os
import grp
import pwd
import hashlib

# from ansible.module_utils import distro
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}


class GlauthCertificates(object):
    """
        Main Class
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.source = module.params.get("source")
        self.destination = module.params.get("destination")
        self.owner = module.params.get("owner")
        self.group = module.params.get("group")

        self.ssl_cert = self.source.get("ssl_cert", None)
        self.ssl_key  = self.source.get("ssl_key", None)

        self.ssl_files = []
        if self.ssl_cert:
            self.ssl_files.append(self.ssl_cert)
        if self.ssl_key:
            self.ssl_files.append(self.ssl_key)

    def get_file_ownership(self, filename):
        return (
            pwd.getpwuid(os.stat(filename).st_uid).pw_name,
            grp.getgrgid(os.stat(filename).st_gid).gr_name
        )

    def run(self):
        """
        """
        failed = False
        changed = False
        msg = "module init."

        verify_sources, msg = self.verify_source_files()

        if not verify_sources:
            return dict(
                changed=False,
                failed=verify_sources,
                msg=msg
            )

        if len(self.destination) == 0:
            return dict(
                changed=False,
                failed=True,
                msg="The destination directory was not properly defined!"
            )

        result = self.create_destination_directory()

        if not result.get('failed', False):
            changed, failed = self.copy_files()
            if changed:
                msg = "The certificate files have been copied successfully."
            else:
                msg = "The certificate files are up to date."

        return dict(
            failed=failed,
            changed=changed,
            msg=msg
        )

    def verify_source_files(self):
        """
        """
        missing = []

        if len(self.ssl_files) < 2:
            if not self.ssl_cert:
                missing.append("cert")
            if not self.ssl_key:
                missing.append("key")

        if len(missing) > 0:
            return False, f"The source files were not specified completely! The following files are missing: {', '.join(missing)}"

        for f in self.ssl_files:
            if not os.path.exists(f):
                missing.append(f)

        if len(missing) > 0:
            return False, f"The source file(s) does not exist: {', '.join(missing)}"

        return True, ""

    def create_destination_directory(self):
        """
        """
        if os.path.isdir(self.destination):
            return dict(
                failed=False,
                changed=False,
                msg=f"Directory {self.destination} already exists."
            )

        # Create the directory
        try:
            os.makedirs(self.destination, exist_ok = True)
            msg = f"Directory '{self.destination}' created successfully."

            shutil.chown(self.destination, self.owner, self.group)

            return dict(
                failed=False,
                changed=True,
                msg=msg
            )

        except OSError as error:
            msg = f"Directory '{self.destination}' can not be created. ({error})"

            return dict(
                failed=True,
                changed=False,
                msg=msg
            )

    def copy_files(self):
        """
        """
        changed = False
        failed = False

        for f in self.ssl_files:
            differ = True
            s = f
            d = os.path.join(self.destination, os.path.basename(f))

            if os.path.isfile(d):
                differ = self.verify(s, d)

            # self.module.log(msg=f" - {s} -> {d}, differ: {differ}")

            if differ:
                shutil.copyfile(s, d)
                os.chmod(d, 0o0440)
                changed = True

        for root, dirs, files in os.walk(self.destination):
            shutil.chown(root, self.owner, self.group)
            for item in dirs:
                shutil.chown(os.path.join(root, item), self.owner, self.group)
            for item in files:
                shutil.chown(os.path.join(root, item), self.owner, self.group)

        return changed, failed

    def verify(self, source_file, destination_file):
        """
        """
        # self.module.log(msg=f"verify({source_file} : {destination_file})")
        s_checksum = None
        d_checksum = None

        if os.path.isfile(source_file):
            s_checksum = self.__create_checksum_file(source_file)

        if os.path.isfile(destination_file):
            d_checksum = self.__create_checksum_file(destination_file)

        # self.module.log(msg=f" - {s_checksum} : {d_checksum}")

        if s_checksum and d_checksum:
            return not (s_checksum == d_checksum)
        else:
            return False

    def __create_checksum_file(self, filename):
        """
        """
        with open(filename, "r") as d:
            _data = d.read().rstrip('\n')
            return self.__checksum(_data)

    def __checksum(self, plaintext):
        """
        """
        _bytes = plaintext.encode('utf-8')
        _hash = hashlib.sha256(_bytes)
        return _hash.hexdigest()


# ===========================================
# Module execution.
#


def main():
    arguments = dict(
        source=dict(
            required=True,
            type='dict',
        ),
        destination=dict(
            required=True,
            type='path'
        ),
        owner=dict(
            required=False,
            type='str',
            default="mysql"
        ),
        group=dict(
            required=False,
            type='str',
            default="mysql"
        ),
    )
    module = AnsibleModule(
        argument_spec = arguments,
        supports_check_mode = False,
    )

    helper = GlauthCertificates(module)
    result = helper.run()

    module.log(msg="= result: {}".format(result))

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
