# 🔍 ScanNet Downloader

## 📄 Instructions
This tool is developed to download specific sequences from the [ScanNet](http://www.scan-net.org/) dataset. Follow the below instructions:

1. Add all the scan IDs you want to download in the file `scan_ids.txt`, one per line. Subsequent runs will not re-download the data, so feel free to add and remove at later stages.
2. Source your ROS1 environment. This has been tested with ROS Noetic on Ubuntu 20.04.
3. Configure the number of parallel processes in the file `main.py` by updating the variable `NUM_PROCESSES`. Then run `python3 main.py`.

💺 Sit back, relax, and wait for the downloads and conversions to finish.


## 🤖 ROS 
The generated ROS1 bags have the following topics:  
1. `/camera/color/image_raw`
2. `camera/depth/image_raw`
3. `/camera/color/camera_info`
4. `/camera/depth/camera_info`

A folder by the name of `gt/scans/` is also created that stores the ground truth trajectories of each sequence.

Some bag files will fail to generate for some reason. There is some unknown issue/bug. If you figure it out, feel free to update.