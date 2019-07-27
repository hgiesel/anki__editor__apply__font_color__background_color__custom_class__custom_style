# Copyright:  (c) 2019 ignd
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


import os
import re
import pickle
import json
from pprint import pprint as pp

from aqt import mw
from aqt.qt import *
from aqt import editor
from aqt.editor import Editor
from anki.hooks import wrap, addHook
from anki.utils import json
from aqt.utils import showInfo, tooltip

from .config import ButtonOptions
from .colors import hex_to_rgb_tuple, html4colors, css3colors
from .contextmenu import add_to_context
from .shortcuts_buttons_21 import setmycategories, setupButtons21, SetupShortcuts21
from .defaultconfig import defaultconfig


addon_path = os.path.dirname(__file__)
iconfolder = os.path.join(addon_path, "icons")
# don't use settings/meta.json to make it easier to save multiline values
user_files_folder = os.path.join(addon_path, "user_files")
picklefile = os.path.join(user_files_folder, "settings.pypickle")
mjfile = os.path.join(addon_path, "meta.json")
config = defaultconfig.copy()


updatetext = ('The add-on "editor: apply font color, background color '
              'custom class, custom style" was updated.'
              '\n\nThis update brings a new config dialog. The add-on '
              'tries to import your old config. '
              "\n\nIf your version of this add-on is from before 2019-02-19 "
              "your old config will be ignored."
              "\n\nIf your version of this add-on is newer there still might "
              "be some unforseeable problems. This new version won't "
              "change your old-config. Your old config is still in "
              "the file 'meta.json' which is in the folder of this add-on. "
              "\n\nTo view your 'meta.json' go to the add-on manager, select this "
              "add-on and click 'View Files'."
              )


def get_config_from_meta_json():
    global config
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
        showInfo(updatetext)
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


def update_config(config):
    config['maxname'] = 0
    config['maxshortcut'] = 0
    config['context_menu_groups'] = []
    config['maxname'] = 0
    config['maxshortcut'] = 0
    for e in config['v3']:
        if e['Show_in_menu']:
            if e.get('Text_in_menu', False):
                config['maxname'] = max(config['maxname'], len(e["Text_in_menu"]))
                if e['Category'] not in config['context_menu_groups']:
                    config['context_menu_groups'].append(e['Category'])
            if e.get('Hotkey', False):
                config['maxshortcut'] = max(config['maxshortcut'], len(e["Hotkey"]))
    return config


def loaddict():
    global config
    if os.path.isfile(picklefile):
        with open(picklefile, 'rb') as PO:
            try:
                config = pickle.load(PO)
            except:
                showInfo("Error. Settings file not readable")
    else:
        # tooltip("Settings file not found")
        config = get_config_from_meta_json()
    update_style_file_in_media()  # always rewrite the file in case a new profile is used
    config = update_config(config)
    if not os.path.exists(user_files_folder):
        os.makedirs(user_files_folder)


def savedict():
    # prevent error after deleting add-on
    if os.path.exists(user_files_folder):
        with open(picklefile, 'wb') as PO:
            pickle.dump(config, PO)


media_dir = None
css_path = None


def setCssPath():
    global media_dir
    global css_path
    global css_path_Customize_Editor_Stylesheet
    media_dir = mw.col.media.dir()
    css_path = os.path.join(media_dir, "_editor_button_styles.css")
    css_path_Customize_Editor_Stylesheet = os.path.join(media_dir, "_editor.css")


def prepareEditorStylesheet():
    global config
    global css_path
    global css_path_Customize_Editor_Stylesheet
    css1 = ""
    if os.path.isfile(css_path):
        with open(css_path, "r") as css_file:
            css1 = css_file.read()
    css2 = ""
    if os.path.isfile(css_path_Customize_Editor_Stylesheet):
        with open(css_path_Customize_Editor_Stylesheet, "r") as css_file:
            css2 = css_file.read()
    # css2 first in case it contains @import url
    css = css2 + "\n" + css1
    editor_style = "<style>\n{}\n</style>".format(css.replace("%", "%%"))
    editor._html = editor_style + editor._html


def onEditorInit(self, *args, **kwargs):
    """Apply modified Editor HTML"""
    # TODO night mode


def update_style_file_in_media():
    global config
    global css_path
    classes_str = ""
    for e in config["v3"]:
        if e["Category"] in ["class"]:
            classes_str += ("." + str(e["Setting"]) +
                            "{\n" + str(e['Text_in_menu_styling']) +
                            "\n}\n\n"
                            )
        if e["Category"] == "Backcolor (via class)":
            classes_str += ("." + str(e["Setting"]) +
                            "{\nbackground-color: " + str(e['Text_in_menu_styling']) + ";" +
                             "\n}\n\n"
                            )
    with open(css_path, "w") as f:
        f.write(classes_str)


def update_all_templates():
    l = """@import url("_editor_button_styles.css");"""
    for m in mw.col.models.all():
        if l not in m['css']:
            model = mw.col.models.get(m['id'])
            model['css'] = l + "\n\n" + model['css']
            mw.col.models.save(model, templates=True)


def onMySettings():
    global config
    # TODO only call settings dialog if Editor or Browser are not active
    # P: User can install "Open the same window multiple times", "Advanced Browser",
    # my "Add and reschedule" so that these are from different classes.
    # tooltip('Close all Browser, Add, Editcurrent windows.')
    dialog = ButtonOptions(config)
    if dialog.exec_():
        config = dialog.config
        config = update_config(config)
        update_style_file_in_media()
        if dialog.update_all_templates:
            update_all_templates()
        showInfo('Restart Anki so that all changes take effect.')


mw.addonManager.setConfigAction(__name__, onMySettings)


def contextmenu():
    global config
    if config.get("v2_show_in_contextmenu", False):
        addHook("EditorWebView.contextMenuEvent", add_to_context)

addHook("profileLoaded", setCssPath)
addHook("profileLoaded", loaddict)
addHook('unloadProfile', savedict)
addHook("profileLoaded", lambda: setmycategories(Editor))
addHook("profileLoaded", contextmenu)
addHook("setupEditorButtons", setupButtons21)
addHook("setupEditorShortcuts", SetupShortcuts21)

addHook("profileLoaded", prepareEditorStylesheet)
# Editor.__init__ = wrap(Editor.__init__, onEditorInit, "after")
