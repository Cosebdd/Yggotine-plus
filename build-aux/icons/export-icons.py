#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yggotine+ Contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Exports the shipped icon theme from the Inkscape sources in data/icons/source.

Requires rsvg-convert (librsvg), ImageMagick and scour.
"""

import os
import subprocess
import sys

BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
SOURCE_PATH = os.path.join(BASE_PATH, "data", "icons", "source")
THEME_PATH = os.path.join(BASE_PATH, "pynicotine", "gtkgui", "icons", "hicolor")

APPLICATION_ID = "org.yggotine_plus.Yggotine"
VARIANT = "rounded"

# Logical sizes, each also exported at @2 scale. Detail level follows the
# logical size, so 16x16@2 uses the 16px artwork rendered at 32 physical pixels.
SIZES = (16, 24, 32, 48, 64, 128, 256)
SCALES = (1, 2)

# Palette entries. Icons use a handful of flat fills, so an indexed PNG is
# lossless here while being several times smaller than truecolour.
MAX_COLOURS = 256


def master_for(size):
    """Small sizes have hand-tuned artwork with fewer details."""

    if size in {16, 24}:
        return os.path.join(SOURCE_PATH, f"source-{VARIANT}-{size}.svg")

    return os.path.join(SOURCE_PATH, f"source-{VARIANT}.svg")


def render_png(svg_path, pixels, png_path):

    subprocess.run(
        ["rsvg-convert", "-w", str(pixels), "-h", str(pixels), svg_path, "-o", png_path],
        check=True
    )
    # Let the encoder pick the colour type. Forcing png:color-type=3 writes a
    # palette with no tRNS chunk, silently discarding the alpha channel.
    subprocess.run(
        ["magick", png_path, "-strip", "-colors", str(MAX_COLOURS),
         "-define", "png:compression-level=9", png_path],
        check=True
    )


def minify_svg(svg_path, dest_path):

    subprocess.run(
        ["scour", "--quiet", "--enable-id-stripping", "--enable-comment-stripping",
         "--shorten-ids", "--remove-metadata", "--strip-xml-prolog",
         "-i", svg_path, "-o", dest_path],
        check=True
    )


def export_application_icons():

    total = 0
    for size in SIZES:
        for scale in SCALES:
            folder = f"{size}x{size}{'@2' if scale > 1 else ''}"
            dest_folder = os.path.join(THEME_PATH, folder, "apps")
            os.makedirs(dest_folder, exist_ok=True)

            master = master_for(size)
            render_png(master, size * scale, os.path.join(dest_folder, f"{APPLICATION_ID}.png"))
            minify_svg(master, os.path.join(dest_folder, f"{APPLICATION_ID}.svg"))
            total += 1

    return total


def export_scalable_icons():

    dest_folder = os.path.join(THEME_PATH, "scalable", "apps")
    os.makedirs(dest_folder, exist_ok=True)

    minify_svg(os.path.join(SOURCE_PATH, f"source-{VARIANT}.svg"),
               os.path.join(dest_folder, f"{APPLICATION_ID}.svg"))

    for state in ("away", "connect", "disconnect", "msg"):
        minify_svg(os.path.join(SOURCE_PATH, f"source-{state}-{VARIANT}.svg"),
                   os.path.join(dest_folder, f"{APPLICATION_ID}-{state}.svg"))

    symbolic_folder = os.path.join(THEME_PATH, "symbolic", "apps")
    os.makedirs(symbolic_folder, exist_ok=True)
    minify_svg(os.path.join(SOURCE_PATH, f"source-symbolic-{VARIANT}.svg"),
               os.path.join(symbolic_folder, f"{APPLICATION_ID}-symbolic.svg"))


if __name__ == "__main__":
    for command in ("rsvg-convert", "magick", "scour"):
        if not any(os.access(os.path.join(path, command), os.X_OK)
                   for path in os.environ["PATH"].split(os.pathsep)):
            sys.exit(f"{command} is required but was not found")

    folders = export_application_icons()
    export_scalable_icons()
    print(f"Exported application icons to {folders} size folders, plus scalable and symbolic")
