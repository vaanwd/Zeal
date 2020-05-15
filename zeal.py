import functools
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


@functools.total_ordering
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

    def __gt__(self, other):
        return self.name > other.name


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


def query_string(zeal_name, text):
    return "{}:{}".format(zeal_name, text) if zeal_name else text


def status(msg):
    sublime.status_message("Zeal: {}".format(msg))


def open_zeal(query):
    cmd_setting = settings.get('zeal_command', "zeal")
    cmd_path = shutil.which(cmd_setting)
    if not cmd_path:
        sublime.error_message("Could not find your Zeal executable. ({})"
                              '\n\nPlease edit Zeal.sublime-settings'
                              .format(cmd_setting))
        return
    try:
        subprocess.Popen([cmd_path, query])
    except Exception as e:
        status(e)
        raise


def match_languages(languages, scope):
    with_scores = [(lang.score(scope), lang) for lang in languages]
    matching = filter(operator.itemgetter(0), with_scores)
    return map(operator.itemgetter(1), sorted(matching))


class ZealSearchSelectionCommand(sublime_plugin.TextCommand):

    handler = None

    def input(self, args):
        if self.handler:
            return self.handler

    def run(self, edit, zeal_name=None):
        self.handler = None
        text, scope = get_word(self.view)

        if not text:
            status("No word was selected.")
            return

        if zeal_name is None:
            language_dicts = settings.get("languages_user", []) + settings.get("languages", [])
            languages = (Language(**d) for d in language_dicts)
            languages = list(match_languages(languages, scope))

            if len(languages) == 1:
                zeal_name = languages[0].zeal_name

            elif languages:
                self.handler = ZealNameInputHandler(languages, text)
                raise TypeError("required positional argument")  # cause ST to call input()

            else:
                # Determine fallback behavior
                fallback = settings.get('fallback', 'none')
                if fallback == 'stop':
                    sublime.status_message("No Zeal mapping found.")
                    return
                elif fallback == 'none':
                    pass  # leave zeal_name unset
                elif fallback == 'guess':
                    # Find innermost 'source' scope
                    base_scopes = reversed(s for s in scope.split() if s.startswith("source."))
                    if not base_scopes:
                        return
                    base_scope = base_scopes[0]
                    zeal_name = base_scope.split(".")[1]
                    status("No language matched {!r}, guessed {!r}.".format(base_scope, zeal_name))
                else:
                    status("Unrecognized 'fallback' setting.")
                    return

        open_zeal(query_string(zeal_name, text))


class ZealSearchCommand(sublime_plugin.TextCommand):
    def input(self, args):
        if not args.get('text'):
            return SimpleTextInputHandler('text', placeholder="query string")

    def run(self, edit, text):
        open_zeal(None, text)


class SimpleTextInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, param_name, *, placeholder=""):
        self.param_name = param_name
        self._placeholder = placeholder

    def name(self):
        return self.param_name

    def placeholder(self):
        return self._placeholder


class ZealNameInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, languages, text):
        self.languages = languages
        self.text = text

    def placeholder(self):
        return "Select docset"

    def list_items(self):
        return sorted(lang.name for lang in self.languages)

    def preview(self, value):
        lang = next(lang for lang in self.languages if lang.name == value)
        return sublime.Html("Query: <code>{}:{}</code>".format(lang.zeal_name, self.text))
