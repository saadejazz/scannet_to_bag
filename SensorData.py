import os, struct
import numpy as np
import zlib
import imageio
import cv2
import png

COMPRESSION_TYPE_COLOR = {-1:'unknown', 0:'raw', 1:'png', 2:'jpeg'}
COMPRESSION_TYPE_DEPTH = {-1:'unknown', 0:'raw_ushort', 1:'zlib_ushort', 2:'occi_ushort'}
counter = 0

class RGBDFrame():

    def load(self, file_handle):
        global counter
        self.camera_to_world = np.asarray(struct.unpack('f'*16, file_handle.read(16*4)), dtype=np.float32).reshape(4, 4)
        self.timestamp_color = struct.unpack('Q', file_handle.read(8))[0]
        self.timestamp_depth = struct.unpack('Q', file_handle.read(8))[0]
        if self.timestamp_depth == 0:
            counter += 1
            # add microseconds corresponding to 30 fps
            self.timestamp_depth = 33333 + counter * 33333

        self.color_size_bytes = struct.unpack('Q', file_handle.read(8))[0]
        self.depth_size_bytes = struct.unpack('Q', file_handle.read(8))[0]
        self.color_data = b''.join(struct.unpack(f'{self.color_size_bytes}s', file_handle.read(self.color_size_bytes)))
        self.depth_data = b''.join(struct.unpack(f'{self.depth_size_bytes}s', file_handle.read(self.depth_size_bytes)))


    def decompress_depth(self, compression_type):
        if compression_type == 'zlib_ushort':
            return self.decompress_depth_zlib()
        else:
            raise ValueError(f"Unknown depth compression type: {compression_type}")

    def decompress_depth_zlib(self):
        return zlib.decompress(self.depth_data)

    def decompress_color(self, compression_type):
        if compression_type == 'jpeg':
            return self.decompress_color_jpeg()
        else:
            raise ValueError(f"Unknown color compression type: {compression_type}")

    def decompress_color_jpeg(self):
        return imageio.imread(self.color_data)


class SensorData:

    def __init__(self, filename, image_size):
        self.version = 4
        self.load(filename, image_size)

    def load(self, filename, image_size):
        with open(filename, 'rb') as f:
            version = struct.unpack('I', f.read(4))[0]
            assert self.version == version
            strlen = struct.unpack('Q', f.read(8))[0]
            self.sensor_name = b''.join(struct.unpack(f'{strlen}s', f.read(strlen))).decode('utf-8')
            self.intrinsic_color = np.asarray(struct.unpack('f'*16, f.read(16*4)), dtype=np.float32).reshape(4, 4)
            self.extrinsic_color = np.asarray(struct.unpack('f'*16, f.read(16*4)), dtype=np.float32).reshape(4, 4)
            self.intrinsic_depth = np.asarray(struct.unpack('f'*16, f.read(16*4)), dtype=np.float32).reshape(4, 4)
            self.extrinsic_depth = np.asarray(struct.unpack('f'*16, f.read(16*4)), dtype=np.float32).reshape(4, 4)
            self.color_compression_type = COMPRESSION_TYPE_COLOR[struct.unpack('i', f.read(4))[0]]
            self.depth_compression_type = COMPRESSION_TYPE_DEPTH[struct.unpack('i', f.read(4))[0]]
            self.color_width = struct.unpack('I', f.read(4))[0]
            self.color_height = struct.unpack('I', f.read(4))[0]
            self.depth_width = struct.unpack('I', f.read(4))[0]
            self.depth_height = struct.unpack('I', f.read(4))[0]
            self.depth_shift = struct.unpack('f', f.read(4))[0]
            num_frames = struct.unpack('Q', f.read(8))[0]
            self.frames = []
            for i in range(num_frames):
                frame = RGBDFrame()
                frame.load(f)
                self.frames.append(frame)

            self.image_size = image_size
            # scale intrinsics to match image size
            self.intrinsic_color[0, 0] *= self.image_size[1] / self.color_width
            self.intrinsic_color[1, 1] *= self.image_size[0] / self.color_height
            self.intrinsic_color[0, 2] *= self.image_size[1] / self.color_width
            self.intrinsic_color[1, 2] *= self.image_size[0] / self.color_height
            self.intrinsic_depth[0, 0] *= self.image_size[1] / self.depth_width
            self.intrinsic_depth[1, 1] *= self.image_size[0] / self.depth_height
            self.intrinsic_depth[0, 2] *= self.image_size[1] / self.depth_width
            self.intrinsic_depth[1, 2] *= self.image_size[0] / self.depth_height


    def export_depth_images(self, output_path, frame_skip=1):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        print(f'exporting {len(self.frames) // frame_skip} depth frames to {output_path}')
        for f in range(0, len(self.frames), frame_skip):
            depth_data = self.frames[f].decompress_depth(self.depth_compression_type)
            depth = np.frombuffer(depth_data, dtype=np.uint16).reshape(self.depth_height, self.depth_width)
            if self.image_size is not None:
                depth = cv2.resize(depth, (self.image_size[1], self.image_size[0]), interpolation=cv2.INTER_NEAREST)
            with open(os.path.join(output_path, str(self.frames[f].timestamp_depth) + '.png'), 'wb') as file:  # write 16-bit
                writer = png.Writer(width=depth.shape[1], height=depth.shape[0], bitdepth=16)
                depth = depth.reshape(-1, depth.shape[1]).tolist()
                writer.write(file, depth)

    def export_color_images(self, output_path, frame_skip=1):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        print(f'exporting {len(self.frames) // frame_skip} color frames to {output_path}')
        for f in range(0, len(self.frames), frame_skip):
            color = self.frames[f].decompress_color(self.color_compression_type)
            if self.image_size is not None:
                color = cv2.resize(color, (self.image_size[1], self.image_size[0]), interpolation=cv2.INTER_NEAREST)
            imageio.imwrite(os.path.join(output_path, str(self.frames[f].timestamp_depth) + '.jpg'), color)

    def save_mat_to_file(self, matrix, filename):
        with open(filename, 'w') as f:
            for line in matrix:
                np.savetxt(f, line[np.newaxis], fmt='%f')

    def export_poses(self, output_path, frame_skip=1):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        print(f'exporting {len(self.frames) // frame_skip} camera poses to {output_path}')
        for f in range(0, len(self.frames), frame_skip):
            self.save_mat_to_file(self.frames[f].camera_to_world, os.path.join(output_path, str(self.frames[f].timestamp_depth) + '.txt'))

    def export_intrinsics(self, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        print(f'exporting camera intrinsics to {output_path}')
        self.save_mat_to_file(self.intrinsic_color, os.path.join(output_path, 'intrinsic_color.txt'))
        self.save_mat_to_file(self.extrinsic_color, os.path.join(output_path, 'extrinsic_color.txt'))
        self.save_mat_to_file(self.intrinsic_depth, os.path.join(output_path, 'intrinsic_depth.txt'))
        self.save_mat_to_file(self.extrinsic_depth, os.path.join(output_path, 'extrinsic_depth.txt'))
