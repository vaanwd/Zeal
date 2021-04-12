import functools
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


def matching_docsets(scope):
    docset_dicts = settings.get("docsets_user", []) + settings.get("docsets", [])
    docsets = set(Docset(**d) for d in docset_dicts)
    with_scores = [(lang.score(scope), lang) for lang in docsets]
    return [docset for score, docset in sorted(with_scores) if score]


class ZealSearchSelectionCommand(sublime_plugin.TextCommand):

    def input(self, args):
        if 'namespace' not in args:
            text, scope = get_word(self.view)
            if not text:
                return

            namespace = self.resolve_namespace(text, scope)
            if isinstance(namespace, NamespaceInputHandler):
                return namespace
            # If a namespace could be resolved,
            # we need to run the same procedure in `run` again
            # because we can't directly pass values from here.
            # We could cache,
            # but we would need to consider the underlying settings changing.

    def run(self, edit, namespace=None):
        text, scope = get_word(self.view)
        if not text:
            status("No word was selected.")
            return

        if namespace is None:
            namespace = self.resolve_namespace(text, scope)
            if not namespace:
                return
            elif isinstance(namespace, NamespaceInputHandler):
                # Fallback if command was called directly through e.g. a key binding.
                sublime.set_timeout(self.rerun_from_command_palette, 0)
                return

        open_zeal(query_string(namespace, text))

    def rerun_from_command_palette(self):
        self.view.window().run_command(
            "show_overlay",
            {"overlay": "command_palette", "command": "zeal_search_selection"},
        )

    def resolve_namespace(self, text, scope):
        matched_docsets = matching_docsets(scope)

        if len(matched_docsets) == 1:
            return matched_docsets[0].namespace

        elif matched_docsets:
            multi_match = settings.get('multi_match', 'select')
            if multi_match == 'select':
                return NamespaceInputHandler(matched_docsets, text)
            elif multi_match == 'join':
                return ",".join(ds.namespace for ds in matched_docsets)

        else:
            fallback = settings.get('fallback', 'none')
            if fallback == 'stop':
                sublime.status_message("No Zeal mapping found.")
                return None
            elif fallback == 'none':
                return ''
            elif fallback == 'guess':
                # Find innermost base scope
                base_scopes = reversed(s for s in scope.split()
                                       if s.startswith("source.") or s.startswith("text."))
                if not base_scopes:
                    sublime.status_message("No Zeal mapping found and could not guess from scope.")
                    return None
                base_scope = base_scopes[0]
                namespace = base_scope.split(".")[1]
                status("No docset matched {!r}, guessed {!r}.".format(base_scope, namespace))
                return namespace
            else:
                status("Unrecognized 'fallback' setting.")
                return None


class ZealSearchCommand(sublime_plugin.TextCommand):
    def input(self, args):
        if not args.get('text'):
            return SimpleTextInputHandler('text', placeholder="query string")

    def run(self, edit, text):
        open_zeal(text)


class SimpleTextInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, param_name, *, placeholder=""):
        self.param_name = param_name
        self._placeholder = placeholder

    def name(self):
        return self.param_name

    def placeholder(self):
        return self._placeholder


class NamespaceInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, docsets, text):
        self.docsets = docsets
        self.text = text

    def placeholder(self):
        return "Select docset"

    def list_items(self):
        return sorted((lang.name, lang.namespace) for lang in self.docsets)

    def preview(self, value):
        return sublime.Html("Query: <code>{}:{}</code>".format(value, self.text))
