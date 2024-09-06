import os
import urllib.request 
import tempfile

import ssl 
ssl._create_default_https_context = ssl._create_unverified_context

BASE_URL = 'http://kaldir.vc.in.tum.de/scannet/'
RELEASES = ['v2/scans', 'v1/scans']
RELEASES_NAMES = ['v2', 'v1']
RELEASE = RELEASES[0]
RELEASE_NAME = RELEASES_NAMES[0]
V1_IDX = 1


def get_release_scans(release_file):
    scan_lines = urllib.request.urlopen(release_file)
    scans = []
    for scan_line in scan_lines:
        scan_id = scan_line.decode('utf8').rstrip('\n')
        scans.append(scan_id)
    return scans
release_file = BASE_URL + RELEASE + '.txt'
release_scans = get_release_scans(release_file)
release_test_file = BASE_URL + RELEASE + '_test.txt'
release_test_scans = get_release_scans(release_test_file)


def download_file(url, out_file):
    out_dir = os.path.dirname(out_file)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    if not os.path.isfile(out_file):
        print('\t' + url + ' > ' + out_file)
        fh, out_file_tmp = tempfile.mkstemp(dir=out_dir)
        f = os.fdopen(fh, 'w')
        f.close()
        urllib.request.urlretrieve(url, out_file_tmp)
        os.rename(out_file_tmp, out_file)
    else:
        print('WARNING: skipping download of existing file ' + out_file)

def download_scan(scan_id, out_dir, skip_existing=False):
    print('Downloading ScanNet ' + RELEASE_NAME + ' scan ' + scan_id + ' ...')
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    ft = ".sens"
    is_test_scan = scan_id in release_test_scans
    v1_sens = not is_test_scan
    if scan_id not in release_scans and not is_test_scan:
        print('ERROR: Invalid scan id: ' + scan_id)
    url = BASE_URL + RELEASE + '/' + scan_id + '/' + scan_id + ft if not v1_sens else BASE_URL + RELEASES[V1_IDX] + '/' + scan_id + '/' + scan_id + ft
    out_file = out_dir + '/' + scan_id + ft
    if skip_existing and os.path.isfile(out_file):
        return
    download_file(url, out_file)
    print('Downloaded scan ' + scan_id)

