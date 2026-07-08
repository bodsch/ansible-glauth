#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Ansible module (backend implementation) to deploy GlAuth TLS certificate
and key files.

Copies TLS certificate/key pairs from a source location into a
destination directory used by GlAuth, ensuring correct ownership and
file permissions. Files are only re-copied when their content differs
from the existing destination copy (verified via a SHA-256 checksum
comparison).

(c) 2025-2026, Bodo Schulz <bodo@boone-schulz.de>
"""

from __future__ import annotations

import grp
import hashlib
import os
import pwd
import shutil
from typing import Any, Dict, List, Optional, Tuple

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: glauth_tls_certificates
short_description: Deploy GlAuth TLS certificate and key files
description:
  - Copies a TLS certificate/key pair from a source location into a
    destination directory used by GlAuth.
  - Files are compared via SHA-256 checksum and are only re-copied when
    their content differs from the existing destination copy (or when
    the destination does not yet exist).
  - The destination directory is created if missing, and ownership of
    the full destination tree is set to the configured I(owner) /
    I(group) after every run. Copied files are set to mode C(0440).
version_added: "1.0.0"
author:
  - Bodo Schulz (@bodsch)
options:
  source:
    description:
      - Dictionary containing the paths to the source certificate and
        key files.
    type: dict
    required: true
    suboptions:
      ssl_cert:
        description: Path to the source TLS certificate file.
        type: str
        required: true
      ssl_key:
        description: Path to the source TLS private key file.
        type: str
        required: true
  destination:
    description:
      - Directory the certificate and key files are copied into.
    type: path
    required: true
  owner:
    description:
      - User that should own the destination directory and copied files.
    type: str
    default: mysql
  group:
    description:
      - Group that should own the destination directory and copied files.
    type: str
    default: mysql
notes:
  - Both C(ssl_cert) and C(ssl_key) must be specified in C(source), and
    both files must already exist on the controller/target - otherwise
    the module fails without changing anything.
  - Copied files are always written with mode C(0440), regardless of
    the source file's original permissions.
"""

EXAMPLES = r"""
- name: Deploy GlAuth TLS certificate and key
  glauth_tls_certificates:
    source:
      ssl_cert: /etc/pki/tls/certs/glauth.crt
      ssl_key: /etc/pki/tls/private/glauth.key
    destination: /etc/glauth/tls
    owner: glauth
    group: glauth
"""

RETURN = r"""
failed:
  description: Whether the module execution failed.
  type: bool
  returned: always
  sample: false
changed:
  description: Whether any certificate file was (re-)copied, or the destination directory was created.
  type: bool
  returned: always
  sample: true
msg:
  description: Human-readable result message.
  type: str
  returned: always
  sample: "The certificate files have been copied successfully."
"""

#: Standard Ansible module result dictionary (`failed`, `changed`, `msg`, ...).
ModuleResult = Dict[str, Any]


class GlauthCertificates:
    """
    Deploys GlAuth TLS certificate and key files into a target directory.

    Source and destination files are compared via SHA-256 checksum; a
    file is only copied when its content differs (or the destination
    does not yet exist). After copying, ownership of the full
    destination tree is set to the configured owner/group, and file
    permissions are restricted to ``0o440``.

    :param module: The active :class:`AnsibleModule` instance, used for
        parameter access and logging.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the instance from the Ansible module parameters.

        :param module: The active AnsibleModule instance.
        """
        self.module: AnsibleModule = module

        self.source: Dict[str, str] = module.params.get("source") or {}
        self.destination: str = module.params.get("destination")
        self.owner: str = module.params.get("owner")
        self.group: str = module.params.get("group")

        self.ssl_cert: Optional[str] = self.source.get("ssl_cert")
        self.ssl_key: Optional[str] = self.source.get("ssl_key")
        self.ssl_files: List[str] = [f for f in (self.ssl_cert, self.ssl_key) if f]

    def run(self) -> ModuleResult:
        """
        Execute the certificate deployment workflow.

        Validates the source files, ensures the destination directory
        exists, and copies changed files into it.

        :return: A dict with keys ``failed``, ``changed`` and ``msg``,
            matching the Ansible module result contract.
        """
        verified, msg = self.verify_source_files()
        if not verified:
            return dict(failed=True, changed=False, msg=msg)

        if not self.destination:
            return dict(
                failed=True,
                changed=False,
                msg="The destination directory was not properly defined!"
            )

        dir_result = self.create_destination_directory()
        if dir_result.get("failed", False):
            return dir_result

        changed, failed = self.copy_files()

        if failed:
            msg = getattr(self, "_last_error", "Failed to copy certificate files.")
        elif changed:
            msg = "The certificate files have been copied successfully."
        else:
            msg = "The certificate files are up to date."

        return dict(failed=failed, changed=changed, msg=msg)

    def verify_source_files(self) -> Tuple[bool, str]:
        """
        Validate that both source files are configured and exist on disk.

        :return: Tuple of ``(is_valid, message)``. ``message`` is empty
            when validation succeeds.
        """
        missing: List[str] = []
        if not self.ssl_cert:
            missing.append("cert")
        if not self.ssl_key:
            missing.append("key")

        if missing:
            return False, (
                "The source files were not specified completely! "
                f"The following files are missing: {', '.join(missing)}"
            )

        missing = [f for f in self.ssl_files if not os.path.exists(f)]
        if missing:
            return False, f"The source file(s) does not exist: {', '.join(missing)}"

        return True, ""

    def create_destination_directory(self) -> ModuleResult:
        """
        Ensure the destination directory exists with the correct ownership.

        :return: A dict with keys ``failed``, ``changed`` and ``msg``.
        """
        if os.path.isdir(self.destination):
            return dict(
                failed=False,
                changed=False,
                msg=f"Directory {self.destination} already exists."
            )

        try:
            os.makedirs(self.destination, exist_ok=True)
            shutil.chown(self.destination, self.owner, self.group)

            return dict(
                failed=False,
                changed=True,
                msg=f"Directory '{self.destination}' created successfully."
            )
        except OSError as error:
            return dict(
                failed=True,
                changed=False,
                msg=f"Directory '{self.destination}' can not be created. ({error})"
            )

    def copy_files(self) -> Tuple[bool, bool]:
        """
        Copy source files into the destination when their content changed.

        Existing files are compared via SHA-256 checksum; only files that
        differ (or do not yet exist at the destination) are copied.
        Afterwards, permissions are set to ``0o440`` and ownership of the
        full destination tree is normalized to the configured
        owner/group.

        Fix vs. legacy implementation: I/O errors (``shutil.copyfile``,
        ``shutil.chown``) are now caught and reported via ``failed=True``
        instead of propagating an uncaught exception or being silently
        ignored.

        :return: Tuple of ``(changed, failed)``.
        """
        changed = False

        try:
            for source_file in self.ssl_files:
                destination_file = os.path.join(self.destination, os.path.basename(source_file))

                differs = True
                if os.path.isfile(destination_file):
                    differs = self.verify(source_file, destination_file)

                if differs:
                    shutil.copyfile(source_file, destination_file)
                    os.chmod(destination_file, 0o440)
                    changed = True

            for root, dirs, files in os.walk(self.destination):
                shutil.chown(root, self.owner, self.group)
                for item in dirs + files:
                    shutil.chown(os.path.join(root, item), self.owner, self.group)

        except (OSError, LookupError) as error:
            self._last_error = f"Failed to copy certificate files: {error}"
            return changed, True

        return changed, False

    def verify(self, source_file: str, destination_file: str) -> bool:
        """
        Compare a source and destination file via SHA-256 checksum.

        :param source_file: Path to the source file.
        :param destination_file: Path to the destination file.
        :return: ``True`` if the files differ, or if a checksum could not
            be computed for one side; ``False`` if they are identical.
        """
        source_checksum = self.__create_checksum_file(source_file) if os.path.isfile(source_file) else None
        destination_checksum = self.__create_checksum_file(destination_file) if os.path.isfile(destination_file) else None

        if source_checksum and destination_checksum:
            return source_checksum != destination_checksum
        return False

    def get_file_ownership(self, filename: str) -> Tuple[str, str]:
        """
        Return the owning user and group name of a file.

        :param filename: Path to the file to inspect.
        :return: Tuple of ``(owner_name, group_name)``.
        """
        stat = os.stat(filename)
        return (
            pwd.getpwuid(stat.st_uid).pw_name,
            grp.getgrgid(stat.st_gid).gr_name,
        )

    def __create_checksum_file(self, filename: str) -> str:
        """
        Compute the SHA-256 checksum of a file's text content.

        :param filename: Path to the file to hash.
        :return: Hex-encoded SHA-256 digest (trailing newline stripped).
        """
        with open(filename, "r") as handle:
            return self.__checksum(handle.read().rstrip("\n"))

    def __checksum(self, plaintext: str) -> str:
        """
        Compute the SHA-256 hex digest of a string.

        :param plaintext: The text to hash.
        :return: Hex-encoded SHA-256 digest.
        """
        return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def main() -> None:
    """
    Ansible module entry point.

    Defines the module argument specification, executes
    :class:`GlauthCertificates`, and reports the result back to Ansible.
    """
    arguments = dict(
        source=dict(required=True, type="dict"),
        destination=dict(required=True, type="path"),
        owner=dict(required=False, type="str", default="mysql"),
        group=dict(required=False, type="str", default="mysql"),
    )
    module = AnsibleModule(argument_spec=arguments, supports_check_mode=False)

    helper = GlauthCertificates(module)
    result = helper.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
