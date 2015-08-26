# DEFCONBOTS 2014/15 (and MakerFaire 2014) Code

This repo contains all the code for the laser turrets used for DEFCONBOTS 2014/15 as well as the Laser Shooting Gallery shown in MakerFaire Bay Area 2014.

**NOTE:** This code is not all well documented, so use at your own risk. I'll add more info as I have time. Feel free to ask for more info if you need it.

## [DEFCONBOTS](http://alvarop.com/2015/08/laser-turret-v2-part-1-overview/)
### Firmware
* **[fw/turretController/](fw/turretController/)** - STM32F4 Discovery board firmware to control various turrets using gearmotors. (Used in DEFCONBOTS 2014)
* **[fw/galvoController/](fw/galvoController/)** - STM32F4 Discovery board firmware to control galvanometer/mirrors and laser  . (Used in DEFCONBOTS 2015)

### Software
* **[sw/turretVision_2.0/](sw/turretVision_2.0/)** - Python openCV/SimpleCV scripts used for targeting/control during DEFCONBOTS 2014
* **[sw/galvoVision/](sw/galvoVision/)** - Python openCV scripts used for calibration, testing, and aiming using during DEFCONBOTS 2015
    * **[sw/galvoVision/calibrate.py](sw/galvoVision/calibrate.py)** - Script used to calibrate laser/camera
    * **[sw/galvoVision/simpleClickTest.py](sw/galvoVision/simpleClickTest.py)** - Script used to test camera calibration. User can click on the image and the laser \*should\* move there.
    * **[sw/galvoVision/target_detection.py](sw/galvoVision/target_detection.py)** - Script used to detect targets using motion detection, color matching, etc. Used during DEFCONBOTS 2015.
    * **[sw/galvoVision/planB.py](sw/galvoVision/target_detection.py)** - Script used to detect targets the 'dumb' way. Counting number of colored pixels in a region and shooting at it. Used during DEFCONBOTS 2015.
    * **[sw/galvoVision/planC.py](sw/galvoVision/target_detection.py)** - Same as planB, but using a video file as an input, instead of the camera.

## [MakerFaire](http://alvarop.com/2014/05/maker-faire-2014/)
### Firmware
* **[fw/targetController/](fw/targetController/)** - STM32F4 Discovery board firmware to control targets and hit detection. (Used in MakerFaire Bay Area 2014)

### Software
* **[sw/targetController/](sw/targetController/)** - Python scripts used for laser shooting gallery game control and scoring. (Used in MakerFaire Bay Area 2014)
