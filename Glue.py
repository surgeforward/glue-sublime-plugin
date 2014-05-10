#!/usr/bin/env python
import sublime, sublime_plugin
import os, webbrowser, json
import urllib

# compatibility with urlopen method for python < 3.0
try:
    from urllib.request import urlopen
    import urllib.parse
except ImportError:
    from urllib2 import urlopen

class GlueCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        ''' '''
        Snippet = GlueSnippet(
            regions=self.selectedRegions(),
            filename=self.getFilename()
        ).save()

        if Snippet.saved():
            Snippet.clipboard()
            Snippet.notify()
            Snippet.show()
        else:
            Snippet.error()

    def selectedRegions(self):
        ''' returns all selected areas in currently active sublime text file '''
        parts = []
        for region in self.view.sel():
            if not region.empty():
                parts.append(self.view.substr(sublime.Region(region.begin(), region.end())))

        if len(parts) > 0:
            return parts
        return [self.view.substr(sublime.Region(0, self.view.size()))]

    def getFilename(self):
        ''' returns name of currently active sublime text file '''
        filename = self.view.file_name()
        if filename is not None:
            filenames = filename.split(os.sep)
            return filenames[-1]
        return ''

class GlueSublimeText():

    @staticmethod
    def packageSetting(key):
        ''' returns value for key in glue sublime package settings '''
        s = sublime.load_settings("Glue.sublime-settings")
        if s and s.has(key):
            return s.get(key)
        return False

class GlueSnippet():

    def __init__(self, filename=None, regions=None):
        ''' snippet initalization '''
        self.sublimeHelper = GlueSublimeText
        self.api_key = self.sublimeHelper.packageSetting('api_key')
        self.paste_url = self.sublimeHelper.packageSetting('paste_url')
        self.filename = filename
        self.regions = regions
        self.lastResult = None
        self.lastError = None

    def url(self):
        ''' returns url for snippet '''
        if not self.lastResult:
            return False
        return self.lastResult.geturl()

    def urlencode(self, data):
        ''' encodes data for http transport using urllib '''
        try:
            return urllib.urlencode(data).encode('utf-8')
        except AttributeError:
            return urllib.parse.urlencode(data).encode('utf-8')

    def show(self, force=False):
        ''' shows current snippet in default web browser '''
        if force is True or self.sublimeHelper.packageSetting('open_in_browser'):
            webbrowser.open_new_tab(self.url())

    def notify(self, error=False):
        ''' '''
        notifyOnSuccess = self.sublimeHelper.packageSetting('notify_on_success')
        if error is False and notifyOnSuccess is False:
            return sublime.status_message('Pasted to Glue: ' + self.url())

        sound = False
        if self.sublimeHelper.packageSetting('notification_sounds'):
            sound = True
        
        termNotifierPath = os.system("which terminal-notifier")
        
        if termNotifierPath is not '' and termNotifierPath is not 1:
            self.notifyOSX(sound, error)
        else:
            self.notifyOther(sound, error)

    def notifyOther(self, sound=False, error=False):
        ''' '''
        if error is not False:
            sublime.error_message(error)
        elif sublime.ok_cancel_dialog('Pasted to Glue: ' + self.url(), 'Go to URL'):
            self.show(True)

    def notifyOSX(self, sound=False, error=False):
        ''' '''
        if sound: sound = '-sound default'
        
        notificationMessage = self.url()
        if error is not False: notificationMessage = error

        notifyClickCommand = ''
        if self.url(): notifyClickCommand = "-execute 'open "+self.url()+"'"

        os.system("terminal-notifier -sender com.sublimetext.3 -title 'Pasted to Glue' -message '"+notificationMessage+"' "+sound+" "+notifyClickCommand)

    def clipboard(self):
        ''' '''
        if self.sublimeHelper.packageSetting('save_to_clipboard'):
            sublime.set_clipboard(self.url())

    def hasAPIKey(self):
        if not self.api_key or self.api_key == 'APIKEYGOESHERE':
            self.lastError = 'Please enter a valid API key!'
            return False
        return True

    def hasPasteURL(self):
        if not self.paste_url:
            self.lastError = 'Please enter a valid paste url!'
            return False
        return True
    
    def save(self):

        if self.hasAPIKey() and self.hasPasteURL():

            data = self.urlencode({ 
                'snippets': json.dumps(self.regions),
                'apiKey': self.api_key,
                'filename': self.filename,
                'redirect': True
            })

            try:
                result = urlopen(self.paste_url, data)
                self.lastResult = result
            except IOError as error:
                self.lastError = error
                self.lastResult = False

        return self

    def error(self):
        ''' returns http error response from last save attempt '''
        if self.sublimeHelper.packageSetting('notify_on_error'):
            self.notify(str(self.lastError))

    def saved(self):
        ''' returns true if snippet has been successfully saved '''
        if not self.lastResult:
            return False
        if self.lastError:
            return False
        return True
