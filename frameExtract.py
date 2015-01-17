"""
frameExtract.py - Simple python program for extracting images at specified
times from a larger video. Includes a graphical interface for choosing
input file, output file locations, and entering times.

"""

import os.path
import subprocess
import tkMessageBox
from Tkinter import *
from tkFileDialog import askopenfilename, askdirectory


FFMPEG_PATH = "/Users/benmarks/Desktop/ffmpeg/ffmpeg"


def getIOSpecs() :
    """
    Get the input and output directories for saving files. 
    """

    # we don't want a full GUI, so keep the root window from appearing
    Tk().withdraw() 
    # show an "Open" dialog box and return the path to the selected file
    inFile = askopenfilename(
        message="Please select a video file for frame extraction.", 
        multiple=False, title="Input Video Selection") 
    if len(inFile) == 0 :
        tkMessageBox.showerror("Invalid Choice",
                               "Must specify an input file")
        exit(1)
    outFile = askdirectory(
        message="Please choose a location for extracted images.",
        title="Output Frame Locations")
    if len(outFile) == 0 :
        tkMessageBox.showerror("Invalid Choice", 
                               "Must specify a output file directory")
        exit(1)

    return inFile , outFile 
    


def callback() :
    """
    Callback function that gets called when the user enters a 
    time to extract.
    """
    master.withdraw()
    userIn = e.get()
    if len( userIn ) > 0 :
        extractFrame( inFile, outFile, userIn )
    
    if not tkMessageBox.askyesno("Continue", 
                                 "Extract another frame?") :
        exit(0)

    master.deiconify()



def runProcess( cmd ) :
    """
    Wrapper around calling other processes from within a Python script.
    """
    process = subprocess.Popen( cmd , 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.STDOUT)
    out, err = process.communicate()
  
    return out

def getFreeFileName(base, extension) :
    """
    Make sure that we are saving with a filename that doesn't already
    exist. This prevents a bug where ffmpeg hangs asking for permission
    to overwrite the existing file (which we don't see).

    Returns a free filename that we should use.
    """

    attempt = base + '.' + extension 
    index = 1

    while os.path.isfile( attempt ) :
        attempt = '{0}-{1}.{2}'.format( base, index, extension )
        index += 1

    return attempt

def extractFrame( inFile, outFile, time ) :
    """
    Extract the image at a given time from the input file, saving
    the result in the outFile directory with a free file name.
    """
    cmd = [ FFMPEG_PATH, \
            "-ss",                                   \
            "OFFSET",                                \
            "-i",                                    \
            "INPUT",                                 \
            "-vframes",                              \
            "1",                                     \
            "OUTPUT",                                \
            "-loglevel",                             \
            "24" \
        ]
    cmd[2] = time
    cmd[4] = inFile 
    cmd[7] = getFreeFileName\
             ( outFile+'/'+inFile.split('/')[-1]+'.'+
               time.replace(":","."), "png")



    out = runProcess( cmd )
    
    if not os.path.isfile( cmd[7] )  :
        if out.find("Output file is empty, nothing was encoded") != -1 :
            tkMessageBox.showerror \
                ("Invalid Time", 
                 "Error getting frame at time {0}.\nNothing was saved."\
                 .format(time))
        
        elif out.find("Could not open file") != -1 :
            tkMessageBox.showerror\
                ("Invalid File Selected",
                 "There was a permissions error when attempting to open the video or save the frame to the selected destination.\n\nPlease ensure you have the necessary permissions.")
            exit(1)

        elif out.find("Invalid duration specification") != -1 :
            tkMessageBox.showerror\
                ("Invalid Time Specified",
                 "The entered time is not in a valid format.\n\nThe format must be hh:mm:ss.xxx")
            

        else :
            tkMessageBox.showerror \
                ("Unknown Error Generating File",
                 "The following program output may be informative: \n\n{0}\n".format( out ) )
    else :

        if out.find("could not seek to position") != -1 : 
            tkMessageBox.showerror \
                ("Invalid Time", 
                 "Error seeking to time {0}.\nScreenshot may not be valid."\
                 .format(time))
        else :

            if tkMessageBox.askyesno\
                ("Success!", 
                 "Image saved to \n\n{0}\nWould you like to open it?"
                 .format(cmd[7])) :
                
                runProcess(['open', cmd[7]])


def main() :
    global e, inFile, outFile, master
    
    inFile, outFile = getIOSpecs()
    master = Tk()
    inst = Label(master, 
                 text="""
Enter time offsets into the video where frames should be captured.

Times should be of the form:  hh:mm:ss.xxx
                 
Incomplete times are interpreted as follows:

    XX - Seconds
    YY:XX - Minutes and Seconds
    ZZ:YY:XX - Hours, Minutes, and Seconds
"""
                   )
    inst.pack()
    e = Entry(master)
    e.pack()
    b = Button(master, text="Grab Frame", width=10, command=callback)
    b.pack()


    
    mainloop()




main()
