# Contents
- `heatmap.py`: Taken from 
[Algernon's lot-to-heapmap.py](https://github.com/algernon/ergodox-layout/blob/master/tools/log-to-heatmap.py)
This script has been modified
- `heatmap-layout.*.json`: These define the key layers. They're required for the `heatmap.py`
script and will create a *.json file that can be uploaded to [KLE](http://www.keyboard-layout-editor.com/#/)
to see a heatmap of key usage
- `hid_listen.mac`: Taken from [here](https://www.pjrc.com/teensy/hid_listen.html), this application
will listen for key press logging events if key logging is turned on and print the logs to the
screen

# Usage
To log key presses to a file to be used by `heatmap.py`, navigate to this directory and run
```
./hid_listen.mac > stamped-log
```
to write to a new file or
```
./hid_listen.mac >> stamped-log
```
to append to a file

To then use the text output of `hid_listen`, run the following:
```
python3 heatmap.py ~/qmk_firmware/heatmap/
```
