#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx, Panels, PlaneData

RUN_FULLSCREEN = True

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="PlaneTracker")
        panel = Panels.MainPanel(self)

        if(RUN_FULLSCREEN):
            self.ShowFullScreen(True)
            cursor = wx.Cursor(wx.CURSOR_BLANK)
            self.SetCursor(cursor)
        else:
            self.Size = (800,510)
            self.Show()



def main():
    app = wx.App(0)

    frame = MainFrame()

    app.MainLoop()

if __name__ == '__main__':
    main()