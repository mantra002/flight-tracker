#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Flight-Tracker by Travis Hagen

import json, urllib.request, requests, bs4, colorsys, random, re
from math import sin, cos, sqrt, atan2, radians, degrees

# SET YOUR HOME LAT/LON HERE
HOME_LAT = 0
HOME_LON = 0

EARTH_RADIUS = 6373.0 #KM

class PlaneInfoRepo():
    DB = {}
    ColorList = []
    ColorsUsedList = []
    _currentlySelect = ""

    def __init__(self):
	#his is to generate N number of dissimilar hue-ed colors
        NUMBER_OF_COLORS = 32 #This should be enough... you'll need more colors if you're tracking a lot of planes at once.
        hsv_tuples = [(x*1.0/NUMBER_OF_COLORS, 0.5, 0.9) for x in range(NUMBER_OF_COLORS)]
        self.ColorList = list(map(lambda x: tuple(255 * y for y in colorsys.hsv_to_rgb(*x)), hsv_tuples))
        self.ColorsUsedList = [False] * NUMBER_OF_COLORS
        random.shuffle(self.ColorList)

    #Return the size of the plane DB
    def GetNumberOfTrackedPlanes(self):
        return len(self.DB)
    
    #Make sure nothing is currently "selected" and mark a plane as "selected" in the DB, used for highlighting.
    def SelectSinglePlane(self, hexId):
        if(self._currentlySelect != ""):
            self.DB[self._currentlySelect].Selected = False
        self._currentlySelect = hexId
        self.DB[self._currentlySelect].Selected = True
    
    #Make sure nothing is selected.
    def DeselectSinglePlane(self):
        if (self._currentlySelect != ""):
            self.DB[self._currentlySelect].Selected = False
        self._currentlySelect = ""
    
    #Original method to test the DB class, not really used anymore.
    def GenerateTestRepo(self):
        testData = [["ASA9322", "B738", 28441, 12],
                        ["SW9283", "B742", 35241, 37],
                        ["UA1203", "A320", 12457, 38],
                        ["DL901", "C172", 2645, 42]]
        for d in testData:
            a = PlaneInfo(d[0], d[1], d[2], d[3])
            self.DB.append(a)

    def SortDBByDistance(self):
        self.DB.sort()
    
    #Intial loading of the aircraft.json file
    def LoadJsonIntoRepo(self, filename, useLocalFile = True):
        self.DB = {}
        if(useLocalFile):
            with open(filename) as f:
                data = json.load(f)
        else:
            with urllib.request.urlopen(filename) as url:
                data = json.loads(url.read().decode())
        for a in data["aircraft"]:
            if ("lat" in a and "flight" in a and "alt_baro" in a):
                pi = self.GetPlaneInfoFromJsonList(a)
                pi.LookupFlightData() #Used to get origin and destination
                #Track which colors are used
                unusedColorIndex = self.ColorsUsedList.index(False)
                self.ColorsUsedList[unusedColorIndex] = True
                pi.Color = self.ColorList[unusedColorIndex]
                self.DB[pi.HexID] = pi

    #Update the DB with the current aircraft.json file
    def UpdateRepoFromJson(self, filename, useLocalFile = True):
        if(useLocalFile):
            with open(filename) as f:
                data = json.load(f)
        else:
            with urllib.request.urlopen(filename) as url:
                data = json.loads(url.read().decode())
        for a in data["aircraft"]:
            if ("lat" in a and "flight" in a and "alt_baro" in a):
                pi = self.GetPlaneInfoFromJsonList(a)
                if(pi.HexID in self.DB):
                    pi.Color = self.DB[pi.HexID].Color
                    pi.Selected = self.DB[pi.HexID].Selected
                    pi.PreviousDistance = self.DB[pi.HexID].PreviousDistance
                    pi.PreviousDistance.append(self.DB[pi.HexID].Distance)
                    pi.PreviousBearing = self.DB[pi.HexID].PreviousBearing
                    pi.PreviousBearing.append(self.DB[pi.HexID].Bearing)
                    pi.Origin = self.DB[pi.HexID].Origin
                    pi.Destination = self.DB[pi.HexID].Destination
                else:
                    pi.LookupFlightData()
                    unusedColorIndex = self.ColorsUsedList.index(False)
                    self.ColorsUsedList[unusedColorIndex] = True
                    pi.Color = self.ColorList[unusedColorIndex]
                self.DB[pi.HexID] = pi
        hexIdToDelete = []
        for p in self.DB.values():
            p.LastSeen += 1
            #Drop the plane from the DB if it hasn't been seen for the last 50 updates
            if p.LastSeen > 50:
                usedColorIndex = self.ColorList.index(p.Color)
                self.ColorsUsedList[usedColorIndex] = False
                hexIdToDelete.append(p.HexID)
        for hexId in hexIdToDelete:
            if(self._currentlySelect == hexId):
                self._currentlySelect = ""
            del self.DB[hexId]

    def GetPlaneInfoFromJsonList(self, jsonList):
        pInfo = PlaneInfo()
        pInfo.HexID = jsonList["hex"]
        pInfo.LookupEquipmentType()
        pInfo.FlightNumber = jsonList["flight"].strip()
        pInfo.AltitudeRaw = int(jsonList["alt_baro"])
        pInfo.FormatRawAltitude(pInfo.AltitudeRaw)
        pInfo.Latitude = float(jsonList["lat"])
        pInfo.Longitude = float(jsonList["lon"])
        if "gs" in jsonList:
            pInfo.Speed = int(jsonList["gs"])
        else:
            pInfo.Speed = 0
        pInfo.GetDistanceFromHome()
        pInfo.GetBearingFromHome()
        pInfo.LastSeen = 0

        return pInfo

class PlaneInfo():
    Equipment = ""
    EquipmentLong = ""
    Operator = ""
    Origin = ""
    Destination = ""
    HexID = ""
    FlightNumber = ""
    AltitudeRaw = -1
    AltitudeFormatted = ""
    Latitude = 0
    Longitude = 0
    LastSeen = 0
    Distance = 0
    Bearing = 0
    Speed = 0
    PreviousDistance = []
    PreviousBearing = []
    Color = ()
    ICAO_CACHE_FILE = "assets/plane_cache.dat"
    Selected = False

    def __init__(self, fNum = "", equip = "", alt = 0, dist = 0):
        self.FlightNumber = fNum
        self.Equipment = equip
        self.AltitudeRaw = alt
        self.FormatRawAltitude(alt)
        self.Distance = dist
        self.PreviousDistance = []
        self.PreviousBearing = []

    def __lt__(self, other):
        return self.Distance < other.Distance

    def FormatRawAltitude(self, altRaw):
        if(altRaw >= 10000):
            altRaw = altRaw // 100;
            self.AltitudeFormatted = "FL" + str(altRaw)
        else:
            self.AltitudeFormatted = "{:,}".format(altRaw)

    def LookupFlightData(self):
        print("Have to Lookup Flight Data for " + self.FlightNumber + " from Web...")
        with urllib.request.urlopen("https://flightaware.com/live/flight/" + self.FlightNumber) as url:
            data = str(url.read())
        ori = re.compile(r"setTargeting\(\\'origin\\', \\'([a-zA-Z0-9]*)\\")
        dest = re.compile(r"setTargeting\(\\'destination\\', \\'([a-zA-Z0-9]*)\\")
        origin = ori.findall(data)
        destination = dest.findall(data)
        if(len(origin) > 0):
            origin = origin[0]
        else:
            origin = "???"
        if (len(destination) > 0):
            destination = destination[0]
        else:
            destination = "???"
        self.Origin = origin
        self.Destination = destination

    def LookupEquipmentType(self):
        cachedData = {}
        with open(self.ICAO_CACHE_FILE) as f:
            cachedData = json.load(f)
        if(self.HexID in cachedData):
            self.Equipment = cachedData[self.HexID][0]
            self.EquipmentLong = cachedData[self.HexID][1]
            self.Operator = cachedData[self.HexID][2]
        else:
            #This is probably a bad idea...
            print("Have to Lookup Equipment for " + self.HexID + " from Web...")
            r = requests.post("http://www.gatwickaviationsociety.org.uk/modeslookup.asp", data ={"MSC":self.HexID})
            soup = bs4.BeautifulSoup(r.text, features="html.parser")
            icaoType = soup.find("input", {'id':'DICAOType'}).get('value')
            detailedEquip = soup.find("input", {'id': 'DType'}).get('value')
            operator = soup.find("input", {'id': 'DOperator'}).get('value')
            cachedData[self.HexID] = [icaoType, detailedEquip, operator]
            #cache the plane data so we don't need to lookup the equipment type every time.
            with open(self.ICAO_CACHE_FILE, 'w') as f:
                json.dump(cachedData, f)
            self.Equipment = icaoType
            self.EquipmentLong = detailedEquip

    def GetBearingFromHome(self):
        lat1 = radians(HOME_LAT)
        lon1 = radians(HOME_LON)
        lat2 = radians(self.Latitude)
        lon2 = radians(self.Longitude)

        intialBearingRad = atan2(sin(lon2-lon1)*cos(lat2), cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1))
        self.Bearing = degrees(intialBearingRad)

    def GetDistanceFromHome(self):
        lat1 = radians(HOME_LAT)
        lon1 = radians(HOME_LON)
        lat2 = radians(self.Latitude)
        lon2 = radians(self.Longitude)

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        #haversine formula
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = EARTH_RADIUS * c #In KM

        #Convert to nautical miles
        self.Distance = round(distance * 0.539957,1)

    def GetFormattedString(self):
        #Formats the plane data into a string used for the data table.
        return self.FlightNumber.ljust(7) + "  |  " + self.Equipment.ljust(4) + "  |  " + self.AltitudeFormatted.ljust(5) + "  |  " + str(self.Speed).ljust(3) + "  |  " + str(self.Distance)

