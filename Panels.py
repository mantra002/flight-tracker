#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Flight-Tracker by Travis Hagen

import wx, PlaneData
import wx.lib.stattext
from math import sin, cos, radians, exp

DATA_SOURCE = "http://localhost:8080/data/aircraft.json"
DATA_SOURCE_LOCAL = "assets/aircraft.json"
USE_LOCAL_DATA = False

class MainPanel(wx.Panel):
    planeTableRows = []
    planeDetailRows = []
    PlaneDataRepo = 0
    NUMBER_OF_TABLE_ROWS = 12
    RADAR_SCALING = 133.0 / 40
    RADAR_X_OFFSET = 175
    RADAR_Y_OFFSET = 170
    TABLE_X_WIDTH = 410
    TABLE_Y_ROW_HEIGHT = 30
    TABLE_X_OFFSET = 360
    TABLE_Y_OFFSET = 55
    DETAIL_X_OFFSET = 20
    DETAIL_Y_OFFSET = 350
    DETAIL_Y_ROW_HEIGHT = 25
    DETAIL_X_WIDTH = 310
    NUMBER_OF_DETAIL_ROWS = 4

    def __init__(self, parent):
        super(MainPanel,self).__init__(parent = parent)

        # Setup stuff
        self.PlaneDataRepo = PlaneData.PlaneInfoRepo()
        self.SetDoubleBuffered(True)

        # Setup Background
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.bg = wx.Bitmap("assets/bg.png")
        self._width, self._height = self.bg.GetSize()

        #Prep for Plane Information
        if(USE_LOCAL_DATA):
            self.PlaneDataRepo.LoadJsonIntoRepo(DATA_SOURCE_LOCAL, True)
        else:
            self.PlaneDataRepo.LoadJsonIntoRepo(DATA_SOURCE, False)

        # Setup Labels
        # I had to use wx.lib.stattext.GenStaticText instead of wx.StaticText to get the background color to update properly on Raspian.
        tableHeaders = wx.lib.stattext.GenStaticText(self, wx.ID_ANY, "Flight".ljust(7) + "  |  " + "Type".ljust(4) + "  |  " + "Alt".ljust(5) + "  |  " + "GS".ljust(3)+ "  |  " + "Dist", pos=(self.TABLE_X_OFFSET, self.TABLE_Y_OFFSET), size=(self.TABLE_X_WIDTH,self.TABLE_Y_ROW_HEIGHT))
        tableHeaders.SetFont(wx.Font(pointSize=11, family=wx.FONTFAMILY_DEFAULT, style=wx.NORMAL, weight=wx.FONTWEIGHT_NORMAL, faceName="Space Mono"))
        tableHeaders.SetForegroundColour((255,255,255))
        tableHeaders.SetBackgroundColour((0,0,0))

        #Add place holders for the table of planes
        for i in range(self.NUMBER_OF_TABLE_ROWS):
            self.planeTableRows.append(wx.lib.stattext.GenStaticText(self, wx.ID_ANY, "Test" + str(i), pos=(self.TABLE_X_OFFSET,self.TABLE_Y_OFFSET+40+self.TABLE_Y_ROW_HEIGHT*i), size =(self.TABLE_X_WIDTH,self.TABLE_Y_ROW_HEIGHT)))
            self.planeTableRows[i].SetFont(wx.Font(pointSize=11, family=wx.FONTFAMILY_DEFAULT, style=wx.NORMAL, weight=wx.FONTWEIGHT_NORMAL, faceName="Space Mono"))
            self.planeTableRows[i].SetForegroundColour((255,255,255))
            self.planeTableRows[i].SetBackgroundColour((0, 0, 0))
            self.planeTableRows[i].Bind(wx.EVT_LEFT_UP, self.OnClick)
            self.planeTableRows[i].Bind(wx.EVT_KEY_DOWN, self.OnKey)

        #Add place holders for the details when you select a plane from the list.
        for i in range(self.NUMBER_OF_DETAIL_ROWS):
            self.planeDetailRows.append(TransparentText(self, wx.ID_ANY, "", pos=(self.DETAIL_X_OFFSET,self.DETAIL_Y_OFFSET+self.DETAIL_Y_ROW_HEIGHT*i), style = wx.ST_NO_AUTORESIZE | wx.TRANSPARENT_WINDOW, size =(self.DETAIL_X_WIDTH,self.DETAIL_Y_ROW_HEIGHT)))
            self.planeDetailRows[i].SetFont(wx.Font(pointSize=9, family=wx.FONTFAMILY_DEFAULT, style=wx.NORMAL, weight=wx.FONTWEIGHT_NORMAL, faceName="Space Mono"))
            self.planeDetailRows[i].SetForegroundColour((255,255,255))
            self.planeDetailRows[i].SetBackgroundColour((0, 0, 0))
            self.planeDetailRows[i].Bind(wx.EVT_LEFT_UP, self.OnClick)
            self.planeDetailRows[i].Bind(wx.EVT_KEY_DOWN, self.OnKey)

        #Update the table with the current list of planes
        self.UpdatePlaneTable(self.PlaneDataRepo)

        # Events for drawing the BG and Idle Updates
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_LEFT_UP, self.OnClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)

        #Setup Timer
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.EventTimer)
        self.timer.Start(500, oneShot=wx.TIMER_CONTINUOUS)




    def OnClick(self, event):
        if(event.GetEventObject() not in self.planeTableRows):
            self.PlaneDataRepo.DeselectSinglePlane()
            self.HidePlaneDetails()
            event.Skip()
        else:
            #There is probably a better way but I find out what plane you clicked on by looking at the flight number and then finding it in the DB.
            label = event.GetEventObject().Label
            label = str(label).split("|")[0].strip()
            if label != "":
                sortedDb = sorted(self.PlaneDataRepo.DB.items(), key=lambda kv: kv[1])
                for i,t in enumerate(sortedDb):
                    if t[1].FlightNumber == label:
                        tableIndex = i
                        break
                print("Selecting HexID " +sortedDb[tableIndex][1].HexID)
                self.PlaneDataRepo.SelectSinglePlane(sortedDb[tableIndex][1].HexID)
                self.ShowPlaneDetails(sortedDb[tableIndex][1].HexID)
            else:
                self.PlaneDataRepo.DeselectSinglePlane()
                self.HidePlaneDetails()
                event.Skip()
        self.SetFocus()
        self.UpdatePlaneTable(self.PlaneDataRepo)

    def OnEraseBackground(self, evt):
        pass

    def UpdatePlaneTable(self, plane_repo):
        sortedDb = sorted(plane_repo.DB.items(), key=lambda kv:kv[1])
        for i in range(self.NUMBER_OF_TABLE_ROWS):
            if i >= plane_repo.GetNumberOfTrackedPlanes():
                self.planeTableRows[i].SetLabel("")
                self.planeTableRows[i].SetBackgroundColour((0, 0, 0))
            else:
                if(sortedDb[i][1].Selected):
                    self.planeTableRows[i].SetForegroundColour((0,0,0))
                    self.planeTableRows[i].SetBackgroundColour(sortedDb[i][1].Color)
                else:
                    self.planeTableRows[i].SetForegroundColour(sortedDb[i][1].Color)
                    self.planeTableRows[i].SetBackgroundColour((0,0,0))
                self.planeTableRows[i].SetLabel(sortedDb[i][1].GetFormattedString())
            self.planeTableRows[i].Refresh()
        self.Refresh()

    def ShowPlaneDetails(self, hexId):
        self.planeDetailRows[0].SetLabel("Flight Number: ".rjust(15) + self.PlaneDataRepo.DB[hexId].FlightNumber)
        self.planeDetailRows[1].SetLabel("Equipment: ".rjust(15) + self.PlaneDataRepo.DB[hexId].EquipmentLong)
        self.planeDetailRows[2].SetLabel("Operator: ".rjust(15) + self.PlaneDataRepo.DB[hexId].Operator)
        self.planeDetailRows[3].SetLabel("Flying From: ".rjust(15) + self.PlaneDataRepo.DB[hexId].Origin + " -> " + self.PlaneDataRepo.DB[hexId].Destination)

    def HidePlaneDetails(self):
        for row in self.planeDetailRows:
            row.SetLabel("")

    def OnKey(self, event):
        """
        Check for ESC key press and exit is ESC is pressed
        """
        key_code = event.GetKeyCode()
        print("Got Key! " + str(key_code))
        if key_code == wx.WXK_ESCAPE or key_code == 81:
            print("Closing!")
            #This doesn't always close the window... I'm not sure why. Help?
            p = wx.GetTopLevelParent(self)
            p.Close()
        else:
            event.Skip()

    def DrawSinglePlaneIndicator(self, bearing, distance, color, size, gc):
        distance = distance * self.RADAR_SCALING
        brush = wx.Brush(wx.Colour(color))
        pen = wx.Pen(wx.Colour(color))
        gc.SetPen(pen)
        gc.SetBrush(brush)
        x = self.RADAR_X_OFFSET + distance*cos(radians(bearing - 90))
        y = self.RADAR_Y_OFFSET + distance*sin(radians(bearing - 90))
        gc.DrawEllipse(x, y, size, size)

    def OnPaint(self, evt):
        dc = wx.BufferedPaintDC(self)
        self.Draw(dc)

    def EventTimer(self, evt):
        if (USE_LOCAL_DATA):
            self.PlaneDataRepo.UpdateRepoFromJson(DATA_SOURCE_LOCAL, True)
        else:
            self.PlaneDataRepo.UpdateRepoFromJson(DATA_SOURCE, False)
        self.UpdatePlaneTable(self.PlaneDataRepo)

    def Draw(self, dc):
        cliWidth, cliHeight = self.GetClientSize()
        if not cliWidth or not cliHeight:
            return
        dc.Clear()
        dc.DrawBitmap(self.bg, 0, 0)
        gc = wx.GraphicsContext.Create(dc)
        #This will draw a dot for the planes current position (if within 45nm of the center) and an exponentially decaying "tail" of previous positions (also <45nm away).
        for plane in self.PlaneDataRepo.DB.values():
            for (i,prevDist) in enumerate(plane.PreviousDistance):
                opacity = 255*exp(-(len(plane.PreviousDistance) - i)/100)
                if prevDist < 45:
                    self.DrawSinglePlaneIndicator(plane.PreviousBearing[i], prevDist, plane.Color + (opacity,), 2, gc)
            if plane.Distance < 45:
                self.DrawSinglePlaneIndicator(plane.Bearing, plane.Distance, plane.Color, 5, gc)


"""
Static text with transparent background
From: https://www.keacher.com/994/transparent-static-text-in-wxpython/
"""

import wx

class TransparentText(wx.StaticText):
  def __init__(self, parent, id=wx.ID_ANY, label='',
               pos=wx.DefaultPosition, size=wx.DefaultSize,
               style=wx.TRANSPARENT_WINDOW, name='transparenttext'):
    wx.StaticText.__init__(self, parent, id, label, pos, size, style, name)

    self.Bind(wx.EVT_PAINT, self.on_paint)
    self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)
    self.Bind(wx.EVT_SIZE, self.on_size)

  def on_paint(self, event):
    bdc = wx.PaintDC(self)
    dc = wx.GCDC(bdc)

    font_face = self.GetFont()
    font_color = self.GetForegroundColour()

    dc.SetFont(font_face)
    dc.SetTextForeground(font_color)
    dc.DrawText(self.GetLabel(), 0, 0)

  def on_size(self, event):
    self.Refresh()
    event.Skip()