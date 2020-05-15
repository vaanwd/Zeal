import operator
import re
import subprocess
import shutil

import sublime
import sublime_plugin

settings = None


def plugin_loaded():
    global settings
    settings = sublime.load_settings('Zeal.sublime-settings')


class Language:
    """A language configuration item, computing defaults based on the given name."""
    def __init__(self, name, zeal_name=None, selector=None):
        self.name = name
        self.zeal_name = zeal_name or name.lower().replace(" ", "-")
        self.selector = selector or "source.{}".format(self.zeal_name)

    def score(self, scope):
        return sublime.score_selector(scope, self.selector)

    def __repr__(self):
        return (
            "{self.__class__.__name__}"
            "(name={self.name!r}"
            ", zeal_name={self.zeal_name!r}"
            ", selector={self.selector!r}"
            ")".format(self=self)
        )


def get_word(view):
    for region in view.sel():
        if region.empty():
            region = view.word(region)
        text = view.substr(region).strip()
        text = re.sub(r"[/\\{}()<>\[\]|* \t\"']", '', text)  # use word_separators setting?
        if "\n" in text:
            return None, None  # what are you doing?
        elif text:
            scope = view.scope_name(region.begin())
            return text, scope

    return None, None


def open_zeal(language, text):
    cmd_setting = settings.get('zeal_command', "zeal")
    cmd_path = shutil.which(cmd_setting)
    if not cmd_path:
        sublime.error_message("Could not find your Zeal executable. ({})"
                              '\n\nPlease edit Zeal.sublime-settings'
                              .format(cmd_setting))

    cmd = [
        cmd_path,
        "{}:{}".format(language.zeal_name, text) if language else text,
    ]
    try:
        subprocess.Popen(cmd)
    except Exception as e:
        sublime.status_message("Zeal: {}".format(e))
        raise


def match_languages(languages, scope):
    with_scores = [(lang.score(scope), lang) for lang in languages]
    matching = filter(operator.itemgetter(0), with_scores)
    sorted_ = sorted(matching, key=operator.itemgetter(0))
    return map(operator.itemgetter(1), sorted_)


class ZealSearchSelectionCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        text, scope = get_word(self.view)
        if not text:
            sublime.status_message('No word was selected.')
            return

        language_dicts = settings.get("languages_user", []) + settings.get("languages", [])
        languages = (Language(**d) for d in language_dicts)
        languages = list(match_languages(languages, scope))

        if not languages:
            # Find innermost 'source' scope
            base_scopes = reversed(s for s in scope.split() if s.startswith("source."))
            if not base_scopes:
                return
            base_scope = base_scopes[0]
            zeal_name = base_scope.split('.')[1]
            sublime.status_message('No Zeal mapping was found for {!r}, falling back to {!r}.'
                                   .format(base_scope, zeal_name))
            languages = [Language(name=zeal_name.title(), zeal_name=zeal_name)]

        if len(languages) == 1:
            open_zeal(languages[0], text)

        else:
            self.view.window().show_quick_panel(
                [lang.name for lang in languages],
                lambda i: open_zeal(languages[i], text) if i != -1 else None,
                sublime.MONOSPACE_FONT,
            )


class SimpleTextInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, param_name, placeholder=""):
        self.param_name = param_name
        self._placeholder = placeholder

    def name(self):
        return self.param_name

    def placeholder(self):
        return self._placeholder


class ZealSearchCommand(sublime_plugin.TextCommand):
    def input(self, text=None):
        if not text:
            return SimpleTextInputHandler('text', "query string")

    def run(self, edit, text):
        open_zeal(None, text)
