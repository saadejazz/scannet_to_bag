import os
from multiprocessing import Pool

from tools import download_scan, generate_random_string, convert_to_rosbag
from SensorData import SensorData

NUM_PROCESSES = 8

def main():
    # read the text file with the list of scan ids
    os.makedirs("scans", exist_ok=True)
    with open("scan_ids.txt", "r") as f:
        scan_ids = f.readlines()

    # create the pool of processes
    pool = Pool(NUM_PROCESSES)
    pool.map(routine, scan_ids)


def routine(scan_id):
    scan_id = scan_id.strip()
    out_path = "scans/" + scan_id

    # download .sens file
    scan_id = scan_id.strip()
    if os.path.exists(out_path + ".sens"):
        print("Sensor file of " + scan_id + " already exists, skipping...")
    else:
        download_scan(scan_id, "scans")

    # convert .sens file to images, depth, and camera poses
    if os.path.isdir(out_path):
        print("Scan " + scan_id + " already converted, skipping...")
    else:
        temp_path = "scans/" + generate_random_string(10)
        os.makedirs(temp_path)
    
        # get the sensor data
        try:
            sd = SensorData(out_path + ".sens", image_size=(480, 640))
        except Exception as e:
            print("Error reading sensor data for scan " + scan_id, e)
            return

        # start conversion
        sd.export_depth_images(os.path.join(temp_path, 'depth'))
        sd.export_color_images(os.path.join(temp_path, 'color'))
        sd.export_poses(os.path.join(temp_path, 'pose'))
        sd.export_intrinsics(os.path.join(temp_path, 'intrinsic'))

        # move folder to correct location
        os.rename(temp_path, out_path)

    # convert to ros bag
    os.makedirs("gt/scans", exist_ok=True)
    if os.path.exists(out_path + ".bag"):
        print("Rosbag of " + scan_id + " already exists, skipping...")
    else:
        temp_path = "scans/" + generate_random_string(10)
        try:
            convert_to_rosbag(out_path, temp_path + ".bag")
            os.rename(temp_path + ".bag", out_path + ".bag")
        except Exception as e:
            print("Error converting to rosbag for scan " + scan_id, e)
            os.remove(temp_path + ".bag")

if __name__ == "__main__":
    main()