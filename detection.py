# Primary imports
import cv2
import numpy as np

# Common imports
from augmentation import FrameAugmentation
from calibration import CameraCalibration


class MarkerDetection:
    def __init__(self,
                 imread_extensions,
                 videocapture_extensions,
                 opengl_extensions) -> None:

        # Import supported extensions
        self.imread_extensions = imread_extensions
        self.videocapture_extensions = videocapture_extensions
        self.opengl_extensions = opengl_extensions

        # Set up aruco
        self.arucoParams = cv2.aruco.DetectorParameters()
        self.aruco_dictionaries = [
            cv2.aruco.DICT_4X4_50,
            cv2.aruco.DICT_4X4_100,
            cv2.aruco.DICT_4X4_250,
            cv2.aruco.DICT_4X4_1000,
            cv2.aruco.DICT_5X5_50,
            cv2.aruco.DICT_5X5_100,
            cv2.aruco.DICT_5X5_250,
            cv2.aruco.DICT_5X5_1000,
            cv2.aruco.DICT_6X6_50,
            cv2.aruco.DICT_6X6_100,
            cv2.aruco.DICT_6X6_250,
            cv2.aruco.DICT_6X6_1000,
            cv2.aruco.DICT_7X7_50,
            cv2.aruco.DICT_7X7_100,
            cv2.aruco.DICT_7X7_250,
            cv2.aruco.DICT_7X7_1000,
            cv2.aruco.DICT_ARUCO_ORIGINAL,
            cv2.aruco.DICT_APRILTAG_16h5,
            cv2.aruco.DICT_APRILTAG_25h9,
            cv2.aruco.DICT_APRILTAG_36h10,
            cv2.aruco.DICT_APRILTAG_36h11
        ]

    # The receiving function
    def process(self, frame, asset_file, asset_extension,
                screen_width, screen_height):
        return self.aruco_processing(frame, asset_file, asset_extension,
                                     screen_width, screen_height)

    def aruco_processing(self, frame, asset_file, asset_extension,
                         screen_width, screen_height):
        processed_frame = frame.copy()  # Copy the frame to avoid mixing up

        # Loop through aruco dictionaries and aruco corners, apply augmentation
        for arucoDict in self.aruco_dictionaries:
            self.aruco_detection(frame, arucoDict)

            # 4 loops for 4 corners
            for arucoCorner in self.arucoCorners:
                if asset_extension in self.imread_extensions:
                    asset = cv2.imread(asset_file)
                    processed_frame = FrameAugmentation().plain_augmentation(
                        arucoCorner, processed_frame, asset)

                # TODO full length video augmentation
                elif asset_extension in self.videocapture_extensions:
                    _, asset = cv2.VideoCapture(asset_file).read()
                    processed_frame = FrameAugmentation().plain_augmentation(
                        arucoCorner, processed_frame, asset)

                elif asset_extension in self.opengl_extensions:
                    asset = asset_file  # TODO call loading model here
                    processed_frame = FrameAugmentation().volumetric_augmentation(
                        arucoCorner, processed_frame, asset,
                        screen_width, screen_height)

                else:
                    processed_frame = self.aruco_highlightning(
                        processed_frame, arucoCorner)

        return processed_frame

    def aruco_detection(self, frame, arucoDict):
        self.arucoCorners, self.arucoIds, _ = cv2.aruco.detectMarkers(
            frame, cv2.aruco.getPredefinedDictionary(arucoDict),
            parameters=self.arucoParams)

        if self.arucoIds is not None:
            self.aruco_parameters(frame)

    def aruco_np_corners(self, arucoCorner):
        return np.int32(arucoCorner).reshape(-1, 2)

    def aruco_parameters(self, frame):
        for arucoCorner in self.arucoCorners:
            np_aruco_corners = self.aruco_np_corners(arucoCorner)

        self.aruco_side_length = int(np.linalg.norm(
            np_aruco_corners[0] - np_aruco_corners[1]))

        for arucoId in range(len(self.arucoIds)):
            # Update calibration
            _, self.dist, self.mtx, _, _ = CameraCalibration().calibrate()
            self.rvec, self.tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
                self.arucoCorners[arucoId], 0.05, self.mtx, self.dist)

    def aruco_highlightning(self, processed_frame, arucoCorner):
        processed_frame = cv2.polylines(
            processed_frame,
            [self.aruco_np_corners(arucoCorner)],
            isClosed=True,
            color=(0, 255, 0),
            # Second parameter is the thickness ratio
            thickness=int(self.aruco_side_length * 0.01)
        )

        return processed_frame
