"""
fChange.py - detect times that represent changes in a video. The
envisioned use case for this software is if you have a power point
video of an animated slide, and you want to determine the time when
these animations begin.

Ben Marks, January 2015

"""


import re
import os
import subprocess
import argparse
import shutil
import numpy as np
from sys import argv
from PIL import Image
from collections import Counter
from detectPeaks import detect_peaks

class FrameInfo :
    def __init__(self, fileName) :
        self.name = fileName
        self.obj = Image.open(fileName)
        self.hist = self.obj.histogram()
        self.data = self.obj.getdata()

def runProcess( cmd ) :
    # Wrapper for calling programs from Python
    process = subprocess.Popen( cmd , 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT)
    out, err = process.communicate()
    retCode = process.returncode
    return out, retCode

def numPixelDiff( f1, f2, step ) :
    """
    Detects the amount of change in pixel component values between
    two frames, f1 and f2.

    Returns a number of statistics about these changes, including:
    => The total amount of change involving components that changed by
       more than 8 units.
    => The aveage amount of change of all pixels.
    => The average amount of change of all components that changed by
       more than 8 units.
    """
    diff = 0
    means = []
    nonZeroMeans = []
    c = Counter()
    for i in xrange(0, len(f1.data), step) :
        if len( f1.data ) != len( f2.data ) :
            print len(f1.data), len(f2.data)
        for j in range(3) :
            val = abs(f1.data[i][j] - f2.data[i][j])
            if val > 8 :
                diff += val
            c[val] += 1

            means.append( val )
            if val > 8 :
                nonZeroMeans.append( val )
    #print c
    if len(nonZeroMeans) == 0 :
        nonZeroMeans = [0] # Return average of zero if nothing changed

    # Total amount of change
    # Average amount of change - all pixels
    # Average amount of change - only pixels that had change > 8
    return diff, \
        1.0 * sum(means) / len(means), \
        1.0 * sum(nonZeroMeans) / len(nonZeroMeans)


def getFrameRate( fileName ) :

    cmd = [ "ffprobe",
            fileName ]
    out, ret = runProcess( cmd )
    fps_list = re.findall(r', (\d*.?\d*?) fps', out)
    if len( fps_list ) == 0 :
        print "Error: Could not extract fps"
        exit(1)
    if len( fps_list ) > 1 :
        print "Error: Multiple fps found!"
        exit(1)
    fps = float( fps_list[0] ) 
    return fps
        
def extractImages( fileName, rate, factor ) :

    try :
        shutil.rmtree("images")
    except :
        pass
    os.mkdir("images")
    

    cmd = [ "ffmpeg",
            "-i", 
            fileName, 
            "-r", 
            str(rate/factor),
            "images/out-%6d.png" ]
    runProcess(cmd)

    return

def validate( times, proposedTimes, tolerance ) :


    timesList = proposedTimes.split('|')
    timesList = [ float(x) for x in timesList ]

    pairTups = []
    for each in timesList :
        pairTups.append( ( each - tolerance, each + tolerance, each ) )
    
    ret = True
    print "\n\n\n"

    for proposed in pairTups :
        res = False
        for actual in times :
            if actual > proposed[0] and actual < proposed[1] :
                print "Matched proposed time {0:^6s} with detected time"\
                    .format(str(round(proposed[2], 3)) ),
                print "{0:^6s} (diff = {1:^6s})"\
                    .format( 
                        str(round(actual, 3)), 
                        str(round(proposed[2] - actual, 3)) 
                    )
                res = True
        if not res : 
            print "Validation Failed on Time: ", time
            ret = False

    print "\n\n\n"

    return ret

def checkForFFMpeg() :

    ret = 0

    try :
        out, ret = runProcess( ['ffmpeg', '-version'] )
    except :
        ret = 1
    if ret != 0 :
        print "Error: Can't find ffmpeg! Is it installed?"
        print "Exiting on error."
        exit(1)
    print "Verified that ffmpeg is installed."

    try :
        out, ret = runProcess( ['ffprobe', '-version'] )
    except :
        ret = 1
    if ret != 0 :
        print "Error: Can't find ffprobe! Is it installed?"
        print "Exiting on error."
        exit(1)
    print "Verified that ffprobe is installed."

def main() :

    parser = argparse.ArgumentParser\
             (description='Detects timing of changes in PowerPoint Movie')
    parser.add_argument('video', type=str, \
                        help='Video to analyze')

    parser.add_argument('--fpsFactor', type=int,  \
                        default=1, help="Sample every N frames")
    parser.add_argument('--pixelFactor', type=int, \
                         default=25, help="Sample every N pixels")

    parser.add_argument('--validationTimes', type=str, \
                        help='Pipe delimited proposed transition times' )
    parser.add_argument('--validationTolerance', type=float, \
                        help='Acceptable tolerance for difference between \
                        suggested and detected', default=0.25)


    args = parser.parse_args()

    checkForFFMpeg()

    fileName = args.video
    fpsFactor = args.fpsFactor

    print "Determining Frame Rate."
    fps = getFrameRate( fileName )
    print "FPS is: ", fps

    print "Extracting image frames . . . ",
    extractImages( fileName, fps, args.fpsFactor )
    print "  Done"

    images = os.listdir("images")
    images = [ 'images/' + x for x in images ]
    
    print "Reading in image files . ",
    for i in range(len(images)) :
        if not i % 25 :
            print " . ",
        images[i] = FrameInfo( images[i] )
    print " .   Done"


    # How much did pixel values change?
    total_pixel_diff = [0.0]  
    # How much did the average pixel change 
    avg_pixel_diff   = [0.0]  
    # How much did the average changing pixel change
    subset_avg_pixel_diff = [0.0] 

    rolling_avg = [0.0]

    for i in range(1, len(images)) :
        total, avg, subsetAvg = numPixelDiff( images[i-1], images[i], 
                                              args.pixelFactor)
        total_pixel_diff.append( total )
        avg_pixel_diff.append( avg )
        subset_avg_pixel_diff.append( subsetAvg )
        print "{0}\t{1}\t{2:.5f} \t {3:.5f}\t".format(i, total, avg, subsetAvg), 
        if len( subset_avg_pixel_diff ) < 5 :
            print 0.0
            rolling_avg.append(0.0)
        else :
            val = sum( subset_avg_pixel_diff[-5:] ) / 5
            rolling_avg.append(val)
            print val

    detectionList = rolling_avg
    threshold_peak = 4


    # Find peaks that are at least above 6 (emperically determined)
    # and at least validationTolerance seconds from neighboring peaks
    peaks = list( detect_peaks( np.array( detectionList ), \
                                mph=threshold_peak, \
                                mpd= int(fps / args.fpsFactor * \
                                         args.validationTolerance ) ))
    
    # Backtrack to the frame that is below our baseline
    starts = set()
    starts_with_dups = []
    for peak in peaks :
        idx = peak
        while( idx >= 0 and subset_avg_pixel_diff[idx] > 0 ) :
            idx -= 1
        # We have gone back to before the animation began ...
        # We really want the first frame number that has the animation
        starts.add( idx + 1 )
        starts_with_dups.append( idx + 1 )
    starts_cp = starts.copy()
    
    times_str = []
    for x in starts_with_dups :
        if x in starts_cp :
            times_str.append( str(round(x * args.fpsFactor * 1.0 
                                        / fps, 3 ) ) )
            starts_cp.discard( x )
        else :
            times_str.append( " - " )
    

    starts = sorted(list(starts))
    times =  [ round(x * args.fpsFactor * 1.0 / fps, 3) for x in starts ]


    
    print "\n\n\n\n"

    print "{0:^20s}\t{1:^20s}\t{2:^20s}".format("Peak Frame #", \
                                             "Rise Frame #", \
                                             "Rise Start Time" )
    for i in xrange(len(starts_with_dups)) :
        print "{0:^20d}\t{1:^20d}\t{2:^20s}".format( peaks[i], 
                                                     starts_with_dups[i], 
                                                     times_str[i] )


    if args.validationTimes and args.validationTolerance :
        
        if validate( times, args.validationTimes, args.validationTolerance ) :
            print "Test PASS"
        else :
            print "Test FAIL"


    # Clean up after ourselves
    # runProcess( ["rmdir", "images"] )
    shutil.rmtree("images")
    
    #os.system("del /q images")
    #os.system("rmdir /q /s images")
    print "\n\n\n"

main()
