
Animation Detector Program

====  WORKFLOW  ====

      (0) Validate that ffprobe and ffmpeg are installed on the system.

      (1) Open up the input video file with ffprobe to determine fps

      (2) Run ffmpeg to extract frames from the video. By default, 
          extract all frames. If --fpsFactor is specified as N, then
	  extract 1/N of all frames at even intervals.

      (3) For each pair of successive frames extracted, calculate the 
          average change of pixel color values for all pixel color values
	  that changed by at least 8. (range: 0 - 255)

      (4) Compute a running average of the last 5 frames changed.

      (5) Execute peak detection on the running average for a peak
          of height at least 4 that is at least --validationTolerance
	  seconds from the last peak.

      (6) Backtrack from the peaks to determine where the amount of 
          change first exceeded the lower threshold (min change of 8).
	  This is the estimated frame where the animation began.

      (7) Convert the beginning frame numbers to the corresponding
          time offset.

      (8) If a set of pipe delemited times are specified (--validationTimes)
          and a tolerance is specified for deviations (--validationTolerance),
	  then attempt to match every input validation time with a transition
	  that occurs within validationTolerance.

      (9) Output whether all times were successfully matched. 

====  USAGE  ====

usage: fChange.py [-h] [--fpsFactor FPSFACTOR] [--pixelFactor PIXELFACTOR]
                  [--validationTimes VALIDATIONTIMES]
                  [--validationTolerance VALIDATIONTOLERANCE]
                  video

Detects timing of changes in PowerPoint Movie

positional arguments:
  video                 Video to analyze

optional arguments:
  -h, --help            show this help message and exit
  --fpsFactor FPSFACTOR
                        Sample every N frames
  --pixelFactor PIXELFACTOR
                        Sample every N pixels
  --validationTimes VALIDATIONTIMES
                        Pipe delimited proposed transition times
  --validationTolerance VALIDATIONTOLERANCE
                        Acceptable tolerance for difference between suggested
                        and detected
====  REQUIREMENTS  ====

=> Python 2.7
=> Numpy
=> FFMpeg, FFProbe
=> Python Imaging Library (PIL)


====  SAMPLE RUN STRINGS  ====

python fChange.py --pixelFactor 50 --validationTimes "1|2|3" --validationTolerance 0.1 slide_008_960_720.mp4 

python fChange.py --validationTimes "1.000|3.001|5.002|7.003|9.004"  --validationTolerance 0.25 --pixelFactor 50 slide_038_720_540.wmv


====  COMPILING WINDOWS EXECUTABLE  ====

=> Additional Requirements: py2exe

Create a "setup.py" file to use for py2exe:

	from distutils.core import setup
	import py2exe
	import numpy # This is the only step that differs from online tutorials
	setup(console=['fChange.py'])

Compile by running: python setup.py py2exe

The compiled binary is now in dist\fChange.exe

====  SAMPLE RUN STRINGS - WINDOWS EXECUTABLE  ====

fChange.exe --pixelFactor 50 --validationTimes "1|2|3" --validationTolerance 0.1 slide_008_960_720.mp4 

fChange.exe --validationTimes "1.000|3.001|5.002|7.003|9.004"  --validationTolerance 0.25 --pixelFactor 50 slide_038_720_540.wmv
