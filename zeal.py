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
class Docset:
    """A docset configuration item, computing defaults based on the given name.

    Comparison and hashing is reduced to the name attribute only.
    This is important when building sets, as later additions are discarded.
    """
    def __init__(self, name, namespace=None, selector=None):
        self.name = name
        self.namespace = namespace or name.lower().replace(" ", "-")
        self.selector = selector or "source.{}".format(self.namespace)

    def score(self, scope):
        return sublime.score_selector(scope, self.selector)

    def __repr__(self):
        return (
            "{self.__class__.__name__}"
            "(name={self.name!r}"
            ", namespace={self.namespace!r}"
            ", selector={self.selector!r}"
            ")".format(self=self)
        )

    def __gt__(self, other):
        return self.name > other.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


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


def query_string(namespace, text):
    return "{}:{}".format(namespace, text) if namespace else text


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


def match_docsets(docsets, scope):
    with_scores = [(lang.score(scope), lang) for lang in docsets]
    matching = filter(operator.itemgetter(0), with_scores)
    return map(operator.itemgetter(1), sorted(matching))


class ZealSearchSelectionCommand(sublime_plugin.TextCommand):

    handler = None

    def input(self, args):
        if self.handler:
            return self.handler

    def run(self, edit, namespace=None):
        self.handler = None
        text, scope = get_word(self.view)

        if not text:
            status("No word was selected.")
            return

        if namespace is None:
            docset_dicts = settings.get("docsets_user", []) + settings.get("docsets", [])
            docsets = set(Docset(**d) for d in docset_dicts)
            matched_docsets = list(match_docsets(docsets, scope))

            if len(matched_docsets) == 1:
                namespace = matched_docsets[0].namespace

            elif matched_docsets:
                multi_match = settings.get('multi_match', 'select')
                if multi_match == 'select':
                    self.handler = ZealNameInputHandler(matched_docsets, text)
                    raise TypeError("required positional argument")  # cause ST to call input()
                elif multi_match == 'join':
                    namespace = ",".join(ds.namespace for ds in matched_docsets)

            else:
                # Determine fallback behavior
                fallback = settings.get('fallback', 'none')
                if fallback == 'stop':
                    sublime.status_message("No Zeal mapping found.")
                    return
                elif fallback == 'none':
                    pass  # leave namespace unset
                elif fallback == 'guess':
                    # Find innermost 'source' scope
                    base_scopes = reversed(s for s in scope.split() if s.startswith("source."))
                    if not base_scopes:
                        return
                    base_scope = base_scopes[0]
                    namespace = base_scope.split(".")[1]
                    status("No docset matched {!r}, guessed {!r}.".format(base_scope, namespace))
                else:
                    status("Unrecognized 'fallback' setting.")
                    return

        open_zeal(query_string(namespace, text))


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
    def __init__(self, docsets, text):
        self.docsets = docsets
        self.text = text

    def placeholder(self):
        return "Select docset"

    def list_items(self):
        return sorted(lang.name for lang in self.docsets)

    def preview(self, value):
        lang = next(lang for lang in self.docsets if lang.name == value)
        return sublime.Html("Query: <code>{}:{}</code>".format(lang.namespace, self.text))
