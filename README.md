# flight-tracker

Change your reciever lat/lon in the PlaneData.py file, make sure the DATA_SOURCE in the Panels file is pointing to your dump1090 aircraft file, install the font in the assets folder and it should "just work". ESC or Q exits, although it doesn't work all of the time.

Run Gui.py to start the application, it runs in fullscreen by default but this can be configured with the flag:

  RUN_FULLSCREEN = True

at the top of Gui.py.

Requires:
* Python 3
* wxPython (I had trouble installing this with pip3, I used the precompiled wheel here: https://github.com/sctv/wxPython_arm71 )
* dump1090
