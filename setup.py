#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023-2025 Nicotine+ Contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import ast
import os
import shutil
import subprocess

from setuptools import find_packages, setup  # pylint: disable=import-error

# The repository keeps upstream's module name so that merges from Nicotine+ stay
# reviewable. Installing under that name would collide with the nicotine-plus
# package over site-packages, so an installable copy is generated instead.
MODULE_NAME = "pynicotine"
PACKAGED_MODULE_NAME = "pyyggotine"
SCRIPT_NAME = "yggotine"
BUILD_FOLDER_NAME = "build"


def read_module_version():
    """Reads the module's version without importing it.

    setup.cfg cannot use its attr: directive for this, because package_dir points
    at the generated copy, which makes attr: fall back to importing an installed
    nicotine-plus instead of reading the version in this repository.
    """

    base_path = os.path.dirname(os.path.realpath(__file__))
    init_path = os.path.join(base_path, MODULE_NAME, "__init__.py")

    with open(init_path, encoding="utf-8") as file_handle:
        tree = ast.parse(file_handle.read())

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__version__":
                return node.value.value

    raise RuntimeError(f"No __version__ found in {init_path}")


def rename_module_references(file_path):
    """Rewrites module references in a text file.

    Binary files, such as compiled translations and images, are left untouched.
    """

    try:
        with open(file_path, encoding="utf-8") as file_handle:
            data = file_handle.read()

    except UnicodeDecodeError:
        return

    if MODULE_NAME not in data:
        return

    with open(file_path, "w", encoding="utf-8") as file_handle:
        file_handle.write(data.replace(MODULE_NAME, PACKAGED_MODULE_NAME))


def build_packaged_module():
    """Generates the installable copy of the module and its launcher script."""

    base_path = os.path.dirname(os.path.realpath(__file__))
    build_path = os.path.join(base_path, BUILD_FOLDER_NAME)
    packaged_path = os.path.join(build_path, PACKAGED_MODULE_NAME)

    shutil.rmtree(packaged_path, ignore_errors=True)
    shutil.copytree(os.path.join(base_path, MODULE_NAME), packaged_path,
                    ignore=shutil.ignore_patterns("__pycache__"))

    for folder_path, _folder_names, file_names in os.walk(packaged_path):
        for file_name in file_names:
            rename_module_references(os.path.join(folder_path, file_name))

    script_folder_path = os.path.join(build_path, "scripts")
    script_path = os.path.join(script_folder_path, SCRIPT_NAME)

    os.makedirs(script_folder_path, exist_ok=True)
    shutil.copy(os.path.join(base_path, SCRIPT_NAME), script_path)
    rename_module_references(script_path)


def build_translations():
    """Builds .mo translation files in the 'locale' folder of the package."""

    base_path = os.path.dirname(os.path.realpath(__file__))
    locale_path = os.path.join(base_path, MODULE_NAME, "locale")

    with open(os.path.join(base_path, "po", "LINGUAS"), encoding="utf-8") as file_handle:
        languages = file_handle.read().splitlines()

    for language_code in languages:
        lang_folder_path = os.path.join(locale_path, language_code)
        lc_messages_folder_path = os.path.join(lang_folder_path, "LC_MESSAGES")
        po_file_path = os.path.join(base_path, "po", f"{language_code}.po")
        mo_file_path = os.path.join(lc_messages_folder_path, "nicotine.mo")

        if not os.path.exists(lc_messages_folder_path):
            os.makedirs(lc_messages_folder_path)

        for path in (locale_path, lang_folder_path, lc_messages_folder_path):
            with open(os.path.join(path, "__init__.py"), "wb") as file_handle:
                # Create empty file
                pass

        subprocess.check_call(["msgfmt", "--check", po_file_path, "-o", mo_file_path])

    # Merge translations into .desktop and appdata files
    with os.scandir(os.path.join(base_path, "data")) as entries:
        for entry in entries:
            if entry.name.endswith(".desktop.in"):
                subprocess.check_call(["msgfmt", "--desktop", f"--template={entry.path}", "-d", "po",
                                       "-o", entry.path[:-3]])

            elif entry.name.endswith(".appdata.xml.in"):
                subprocess.check_call(["msgfmt", "--xml", f"--template={entry.path}", "-d", "po",
                                       "-o", entry.path[:-3]])


if __name__ == "__main__":
    build_translations()
    build_packaged_module()
    setup(
        version=read_module_version(),
        package_dir={"": BUILD_FOLDER_NAME},
        packages=find_packages(
            where=BUILD_FOLDER_NAME,
            include=[f"{PACKAGED_MODULE_NAME}*"],
            exclude=[f"{PACKAGED_MODULE_NAME}.plugins.examplars*", f"{PACKAGED_MODULE_NAME}.tests*"]
        ),
        scripts=[os.path.join(BUILD_FOLDER_NAME, "scripts", SCRIPT_NAME)]
    )
