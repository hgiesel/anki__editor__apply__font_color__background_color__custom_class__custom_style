# Copyright:  (c) 2019- ignd
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import json
import os
from pprint import pprint as pp

from aqt import mw
from aqt.utils import (
    askUser,
    showInfo,
)


from .colors import html4colors, css3colors
from .vars import addonname, ankiwebpage, mjfile


updatetext_201908 = (f'This is a warning message generated by the add-on {addonname} '
                      'This message is only shown once after the update/installation of this '
                      'add-on or if you use a different profile for the first time.'
                      '\n\nThis add-on got a big update in 2019-08 which brings a new config '
                      'dialog. The add-on tries to import the old config. '
                      "\n\nIf your version of this add-on is from before 2019-02-19 "
                      "your old config will be ignored."
                      "\n\nIf your version of this add-on is newer there still might "
                      "be some unforseeable problems. This new version won't "
                      "change your old-config. Your old config is still in "
                      "the file 'meta.json' which is in the folder of this add-on. "
                      "\n\nTo view your 'meta.json' go to the add-on manager, select this "
                      "add-on and click 'View Files'."
                      "\n\nIf you run into a problem you can report this on"
                      "\nhttps://github.com/ijgnd/anki__quick_highlight_fontcolor_background/issues"
                    )




def read_and_update_old_v2_config_from_meta_json(config):
    """update old v2 config that was used before 2019-08-06"""
    mjconfig = ""
    if os.path.exists(mjfile):
        with open(mjfile, "r") as mjf:
            mj = json.load(mjf)
            if "config" in mj:
                mjconfig = mj['config']
    if mjconfig:
        # check for illegal entries and abort
        v2_entries_bool = ["v2_configwarning",
                           "v2_menu_styling",
                           "v2_show_in_contextmenu",
                           "v2_wider_button_in_menu",
                           ]
        v2_entries_str = ["v2_key_styling_menu"]
        v2_entries_list = ["v2"]
        v2_all = v2_entries_bool + v2_entries_str + v2_entries_list
        v2_contents_bool = ["Show_in_menu",
                            "extrabutton_show",
                            "extrabutton_width",
                            ]
        v2_contents_str = ["Category",
                           "Hotkey",
                           "Setting",
                           "Text_in_menu",
                           "Text_in_menu_styling",
                           "extrabutton_text",
                           "extrabutton_tooltip",
                           ]
        v2_contents_all = v2_contents_bool + v2_contents_str
        for k, v in mjconfig.items():
            if k not in v2_all:
                text = ('Error while reading old config of the add-on "editor: apply '
                        'font color, background color custom class, custom style". '
                        '\n\n Unknown value "%s" detected in config. Ignoring old config.'
                        % str(k)
                        )
                showInfo(text)
                return
            error = False
            if k in v2_entries_bool and not isinstance(v, bool):
                error = True
            if k in v2_entries_str and not isinstance(v, str):
                error = True
            if k in v2_entries_list and not isinstance(v, list):
                error = True
            if error:
                text = ('Error while reading old config of the add-on "editor: apply '
                        'font color, background color custom class, custom style". '
                        '\n\n Illegal value "%s" detected in option %s config. Ignoring old config.'
                        % (str(v), str(k))
                        )
                showInfo(text)
                return
            error = False
            for e in mjconfig['v2']:
                if not isinstance(e, dict):
                    text = ('Error while reading old config of the add-on "editor: apply '
                            'font color, background color custom class, custom style". '
                            '\n\n In "v2" there is an entry that is not a dictionary. '
                            'Ignoring old config.'
                            )
                    showInfo(text)
                    return
                for k, v in e.items():
                    if k not in v2_contents_all:
                        error = (k, "")
                    if k in v2_contents_str and not isinstance(v, str):
                        error = (k, v)
                    if k in v2_contents_bool and not isinstance(v, bool):
                        error = (k, v)
                if error:
                    text = ('Error while reading old config of the add-on "editor: apply '
                            'font color, background color custom class, custom style". '
                            '\n\n Illegal value "%s", "%s" detected in option "v2" config.'
                            'Ignoring old config.'
                            % (str(error[0]), str(error[1]))
                            )
                    showInfo(text)
                    return
        showInfo(updatetext_201908)
        config = mjconfig
        v2 = config['v2']
        # adjust old config
        for i, e in enumerate(v2):
            e["Hotkey"] = e["Hotkey"].lower()
            # convert colors
            if e["Category"] in ["forecolor", "backcolor"]:
                for k, v in html4colors.items():
                    if k == e["Setting"]:
                        e["Setting"] = v
                for k, v in css3colors.items():
                    if k == e["Setting"]:
                        e["Setting"] = v
            # uppercase forecolor, backcolor so that they are sorted together
            for v, k in e.items():
                if v == "Category" and k == "backcolor":
                    v2[i]["Category"] = "Backcolor (inline)"
                if v == "Category" and k == "forecolor":
                    v2[i]["Category"] = "Forecolor"
        config['v3'] = v2
    return config


def autogenerate_config_values_for_menus(config):
    config['maxname'] = 0
    config['maxshortcut'] = 0
    config['context_menu_groups'] = []
    config['maxname'] = 0
    config['maxshortcut'] = 0
    for e in config['v3']:
        if e['Category'] == "class (other)":
            if not "Target group in menu" in e:
                e["Target group in menu"] = ""
        if e['Show_in_menu']:
            if e.get('Text_in_menu', False):
                config['maxname'] = max(config['maxname'], len(e["Text_in_menu"]))
                if e['Category'] == "class (other)" and e["Target group in menu"]:
                    thisgroup = e["Target group in menu"]
                elif e['Category'] == "text wrapper" and e["Target group in menu"]:
                    thisgroup = e["Target group in menu"]
                else:
                    thisgroup = e['Category']
                if thisgroup not in config['context_menu_groups']:
                    config['context_menu_groups'].append(thisgroup)
            if e.get('Hotkey', False):
                config['maxshortcut'] = max(config['maxshortcut'], len(e["Hotkey"]))
    return config


updatetext_202005 = (f"A new version of the add-on '{addonname}' was installed.\n\n"
                      "This new version has multiple improvements such as the option to set "
                      "different colors for night mode or an easy option to set the font size. Also "
                      "classees are applied more reliably.\n\n"
                      "The downside is that some parts of your old config no longer work with the "
                      "most recent add-on version. The parts that no longer work have been "
                      "disabled. You can still see them at the bottom of the add-on config.\n\n"
                      "To see the add-on config dialog: In the main window click on the menu "
                     f'"Tools", then select "Configure {addonname}".\n\n'
                      'You can reenable these deprecated options and they might work but use this '
                      'at your own risk.\n\n'
                      'The option "Backcolor (inline)" and "style" have been disabled '
                      'because when you later copy text from one field to another Anki '
                      'will remove the background color and styles. I had multiple '
                      "complaints about this. By removing these config options you can no longer "
                      "run into this limitation by accident.\n\n"
                      "I removed the config option 'Forecolor' because some colors that look good "
                      "in regular mode don't work in night mode. So I wanted to make it easy to "
                      "change the color for night mode and this didn't work with 'Forecolor'.\n\n"
                      'Instead of "Backcolor (inline)" use "Backcolor (via class)", instead of '
                      '"style" use "class (other)" and instead of "Forecolor" use '
                      '"Forecolor (via class)".\n\n'
                      "I also included an updated default config. If you want to use the new default "
                      "config you can do this from the add-on config dialog by clicking the 'more' "
                      "button in the upper right."
                     )


def uses_most_recent_config(config, level):
    if not "update_level" in config:
        return False
    current = config["update_level"]
    try:
        current = int(current)
    except:
        return False
    else:
        if current > level:
            return True
        else:
            return False


def update_config_for_202005(config):
    """in 2020-05 I changed this:
        - added separate config values for night mode
        - added font size (via class)
        - added Forecolor (via class)
        - removed Backcolor (inline)
        - removed Forecolor
        - removed style
    """
    for e in config['v3']:
        if not "Text_in_menu_styling_nightmode" in e:
            e["Text_in_menu_styling_nightmode"] = ""
    if not "v3_inactive" in config:
        config["v3_inactive"] = []
    if not uses_most_recent_config(config, 1589114109):
        oldv3 = config['v3'][:]
        config['v3'] = []
        showwarning = False
        for row in oldv3:
            if row["Category"] in ["Backcolor (inline)", "Forecolor", "style"]:
                config["v3_inactive"].append(row)
                showwarning = True
            else:
                if row["Category"] == "class":
                    row["Category"] = "class (other)"
                config['v3'].append(row)
        config["update_level"] = 1589114110
        if showwarning:
            showInfo(updatetext_202005)
    return config
