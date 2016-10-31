import sublime
import sublime_plugin
import os
import subprocess
import shutil

language = None


def get_settings():
    zeal_path = sublime.packages_path() + '/Zeal'
    user_path = sublime.packages_path() + '/User'

    if not os.path.isdir(user_path):
        os.mkdir(user_path)

    default_settings_path = zeal_path + '/Zeal.sublime-settings'
    user_settings_path = user_path + '/Zeal.sublime-settings'
    if not os.path.exists(user_settings_path):
        if sublime.version() >= '3000':
            zs = sublime.load_resource("Packages/Zeal/Zeal.sublime-settings")
            with open(user_settings_path, "w") as f:
                f.write(zs)
        else:
            shutil.copyfile(default_settings_path, user_settings_path)

    return sublime.load_settings('Zeal.sublime-settings')


def get_language(view):
    scope = view.scope_name(view.sel()[0].begin()).strip()
    getlang = scope.split('.')
    language = getlang[-1]
    # some langaue like CmakeEditor is cmakeeditor keyword
    language = language.split()[0]
    if language == 'basic':
        language = getlang[-2]
    if language == 'html':
        if 'php' in getlang:
            language = 'php'
        elif 'js' in getlang:
            language = 'javascript'
        elif 'css' in getlang:
            language = 'css'
    if language == 'js':
        language = 'javascript'
    if 'source.css.less' in scope:
        language = 'less'
    if 'source.scss' in scope:
        language = 'scss'
    if 'source.sass' in scope:
        language = 'sass'
    if 'source.actionscript.2' in scope:
        language = 'actionscript'
    if 'source.cmake' in scope:
        language = 'cmake'
    del getlang
    return language


def get_css_class_or_id(view):
    cur_pos = view.sel()[0].a
    scope_reg = view.extract_scope(cur_pos)

    def get_sym(pos):
        sym = view.substr(sublime.Region(pos, pos + 1))
        return sym

    rule_type = set(['.', '#'])
    delims = set([
        ' ', '"', "'", '<', '>', '(', ')', '/', '\n', ':',
    ])
    all_delims = rule_type | delims
    left = cur_pos
    while get_sym(left) in delims:
        left -= 1
    while left > scope_reg.a and get_sym(left) not in all_delims:
        left -= 1
    if get_sym(left) in all_delims:
        left += 1
    right = cur_pos
    while right < scope_reg.b and get_sym(right) not in all_delims:
        right += 1
    return view.substr(sublime.Region(left, right))


def selection(view):

    def IsNotNull(value):
        return value is not None and len(value) > 1

    def badChars(sel):
        bad_characters = [
            '/', '\\', ':', '\n', '{', '}', '(', ')',
            '<', '>', '[', ']', '|', '?', '*', ' ',
            '""', "'",
        ]
        for letter in bad_characters:
            sel = sel.replace(letter, '')
        return sel

    selection = ''
    for region in view.sel():
        selection += badChars(view.substr(region))
    if IsNotNull(selection):
        return selection
    else:
        curr_sel = view.sel()[0]
        word = view.word(curr_sel)
        selection = badChars(view.substr(word))
        if IsNotNull(selection):
            return selection
        else:
            return None
    return None

def selection_erlang(view):
    cur_pos = view.sel()[0].a
    scope_reg = view.line(cur_pos)

    def get_sym(pos):
        sym = view.substr(sublime.Region(pos, pos + 1))
        return sym

    rule_type = set(['.', '#'])
    delims = set([
        ' ', '"', "'", '<', '>', '(', ')', '/', '\n',
    ])
    all_delims = rule_type | delims
    left = cur_pos
    while get_sym(left) in delims:
        left -= 1
    while left > scope_reg.a and get_sym(left) not in all_delims:
        left -= 1
    if get_sym(left) in all_delims:
        left += 1
    right = cur_pos
    while right < scope_reg.b and get_sym(right) not in all_delims:
        right += 1
    return view.substr(sublime.Region(left, right))



def get_word(view):
    word = None
    if language == 'css' or language == 'scss' or language == 'sass' \
        or language == 'less':
        word = get_css_class_or_id(view)
    elif language == 'erlang':
        word = selection_erlang(view)
        print(word)
    else:
        word = selection(view)
    return word


def open_zeal(lang, text, join_command):
    zeal_exe = get_settings().get('zeal_command')

    if os.path.isfile(zeal_exe):
        try:
            cmd = [zeal_exe]
            if join_command or lang is None or lang == '':
                cmd.append(text)
            else:
                cmd.append(lang + ":" + text)
            # Change cwd so that Zeal won't prevent ST updates on Windows
            # where it would hold a handle to the ST directory.
            subprocess.Popen(cmd, cwd=os.path.dirname(zeal_exe))
        except Exception as e:
            sublime.status_message("Zeal - (%s)" % (e))
    else:
        sublime.error_message('Could not find your %s executable.\n\nPlease edit Zeal.sublime-settings' % (zeal_exe))


class ZealSearchSelectionCommand(sublime_plugin.TextCommand):

    def no_word_selected(self):
        sublime.status_message('No word was selected.')

    def run(self, edit, **kwargs):
        global language
        language = get_language(self.view.window().active_view())
        text = ""

        for selection in self.view.sel():
            if selection.empty():
                text = self.view.word(selection)

            text = self.view.substr(selection)

            if text == "":
                text = get_word(self.view)

            if text is None:
                self.no_word_selected()
            else:
                language_mapping = get_settings().get('language_mapping')
                items = dict()
                popup_list = []

                for item in language_mapping.items():
                    if item[1]['lang'] == language:
                        items[item[0]] = item[1]

                if len(items) > 1:
                    srt = None
                    sort_res = get_settings().get('mapping_sort')
                    if(sort_res):
                        import operator
                        srt = sorted(items.items(), key=operator.itemgetter(0))
                    else:
                        srt = items.items()
                    for title, files in srt:
                        popup_list.append([title, 'Language: %s' % (files['lang'])])
                elif len(items) == 1:
                    open_zeal(list(items.values())[0]['zeal_lang'], text, False)
                else:
                    sublime.status_message('No Zeal mapping was found for %s language.' % (language))

            def callback(idx):
                if idx == -1:
                    return
                self.selected_item = popup_list[idx]
                open_zeal(items[self.selected_item[0]]['zeal_lang'], text, False)

            if text:
                if len(kwargs) == 0:
                    self.view.window().show_quick_panel(popup_list, callback, sublime.MONOSPACE_FONT)
                elif len(kwargs) != 0:
                    self.selected_item = kwargs['title']
                    open_zeal(items[self.selected_item]['zeal_lang'], text, False)


class ZealSearchCommand(sublime_plugin.TextCommand):

    last_text = ''

    def run(self, edit):
        view = self.view
        self.view_panel = view.window().show_input_panel('Search in Zeal for:', self.last_text, self.after_input, self.on_change, None)
        self.view_panel.set_name('zeal_command_bar')

    def after_input(self, text):
        if text.strip() == "":
            self.last_text = ''
            sublime.status_message("No text was entered")
            return
        else:
            open_zeal("", text, True)

    def on_change(self, text):
        if text.strip() == "":
            return

        self.last_text = text.strip()
