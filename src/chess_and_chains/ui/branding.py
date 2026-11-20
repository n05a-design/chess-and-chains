"""Local Connected System preview assets for Tk 9 and earlier releases."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
from importlib.resources import files
import tkinter as tk


def brand_image(master: tk.Misc, name: str, *, scale: float = 1) -> tk.PhotoImage:
    assets = files(__package__).joinpath("brand_assets")
    try:
        return tk.PhotoImage(
            master=master, data=assets.joinpath(f"{name}.svg").read_bytes(),
            format=("svg", "-scale", scale),
        )
    except tk.TclError:
        # Tk 8.6 has PNG support but no native SVG reader.
        png = base64.b64encode(assets.joinpath(f"{name}.png").read_bytes())
        return tk.PhotoImage(master=master, data=png, format="png")
