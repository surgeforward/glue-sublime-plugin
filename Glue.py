#!/usr/bin/env python
import sublime, sublime_plugin, urllib, os, webbrowser, json, pprint

try:
    from urllib.request import urlopen
    import urllib.parse
except ImportError:
    from urllib2 import urlopen

class GlueCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        ''' '''
        sublimeHelper = GlueSublimeText
        regions = self.selectedRegions()
        filename = self.getFilename()
        Snippet = GlueSnippet(regions=regions, filename=filename)
        Snippet.save()

        if Snippet.saved():
            # use sublime module to set users clipboard to new url
            url = Snippet.url()
            sublime.set_clipboard(url)
            sublime.status_message('Glued: ' + url)

            # check if users package settings, allow us to open new snippet in browser
            if sublimeHelper.packageSetting('open_in_browser'):
                Snippet.show()

            return True
        
        # error has occured, retrieve from snippet and send to user via sublime text module
        sublime.status_message('An error has occurred: ' + Snippet.error())

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
        self.sublimeHelper = GlueSublimeText
        self.api_key = self.sublimeHelper.packageSetting('api_key')
        self.paste_url = self.sublimeHelper.packageSetting('paste_url')
        self.filename = filename
        self.regions = regions
        self.lastResult = None

    def urlencode(self, data):
        ''' encodes data for http transport using urllib '''
        try:
            return urllib.urlencode(data).encode('utf-8')
        except AttributeError:
            return urllib.parse.urlencode(data).encode('utf-8')

    def show(self):
        ''' shows current snippet in default web browser '''
        return webbrowser.open_new_tab(self.url())

    def url(self):
        ''' returns url for snippet '''
        if not self.lastResult:
            return False
        return self.lastResult.geturl()

    def saved(self):
        ''' returns true if snippet has been successfully saved '''
        if not self.lastResult:
            return False
        return True

    def save(self):
        data = self.urlencode({ 
            'snippets': json.dumps(self.regions),
            'apiKey': self.api_key,
            'filename': self.filename,
            'redirect': True
        })

        result = urlopen(self.paste_url, data)
        self.lastResult = result
        return result
