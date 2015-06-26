from gtk.gdk import __init__

__author__ = 'shiriiin'

import Leap
import sys
import thread
import time
import math
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture


class LeapMotionListener(Leap.Listener):
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
    state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']
    connected_flag = False  # True if device is connected
    frameAvailable_flag = False  # True if there is a new frame of data available
    current_frame_id = None  # ID of the most recent frame of data
    agent_is_flying = False
    agent_mouse_look = False
    direct = None
    walking = None
    #  frame = None
    #  listener = None
    #  controller = None

    #  def __init__(self):
        #  self.listener = LeapMotionListener()
        #  self.controller = Leap.Controller()
        #  self.frame = self.controller.frame()
        #  Detect Most Recent Frame
        #  controller.frame(0) is the most recent one and controller.frame(1)
        #  is the previous one
        #  self.controller.add_listener(self.listener)

    def on_init(self, controller):
        print "Initialized"

    def on_connect(self, controller):
        print "Motion Sensor Connected!"
        self.connected_flag = True
        self.current_frame_id = 0

        # Enable Gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def on_disconnect(self, controller):
        print "Motion Sensor Disconnected!"
        self.connected_flag = False

    def on_exit(self, controller):
        print "Exited"

    # TODO: Return speed motion base on fingers angle
    def speed_detection(self, controller):
        pass

    # TODO: Detect specific gesture to move forward
    def move_forward(self, controller):
        if self.walking:
            print "start walking!"
        else:
            print "Stop walking!"

    # TODO: Detect specific gesture to change avatar direction
    def change_direction(self, controller):
        if self.direct == "Left":
            print "GO LEFT!"
        elif self.direct == "Forward":
            print "GO FORWARD!"
        elif self.direct == "Right":
            print "GO RIGHT!"

    # TODO: Detect specific gesture to change avatar mode (fly or walk)
    def change_mode(self, controller):
        if self.agent_is_flying:
            self.agent_is_flying = False
            print "Avatar is walking!"
        else:
            self.agent_is_flying = True
            print "Avatar is flying!"

    # TODO: Detect specific gesture to change avatar view mode(mouse look or not!)
    def change_view_mode(self, controller):
        if self.agent_mouse_look:
            self.agent_mouse_look = False
            print "Avatar is in normal mode!"
        else:
            self.agent_mouse_look = True
            print "Avatar is in mouse look mode!"

    def on_frame(self, controller):
        if self.connected_flag:
                frame = controller.frame()
                #  frame_id = frame.id()
                #  if frame_id != self.current_frame_id:
                #      self.current_frame_id = frame_id
                #      self.frameAvailable_flag = True
                for hand in frame.hands:  # List of Hands in Frame
                    position = hand.palm_position
                    if 87 <= position[1] <= 93:
                        self.walking = True
                        self.move_forward(self)
                        direction = hand.direction  # Direction Vector
                        direction_detection = direction.yaw * Leap.RAD_TO_DEG
                        if direction_detection <= -11:
                            self.direct = "Left"
                            self.change_direction(self)
                        elif -10 <= direction_detection <= 10:
                            self.direct = "Forward"
                            self.change_direction(self)
                        elif 11 <= direction_detection:
                            self.change_direction(self)
                            self.direct = "Right"
                #    normal = hand.palm_normal  # Normal Vector
                #      hand_type = "Left Hand" if hand.is_left else "Right Hand"
                #      print hand_type
                #      print hand_type + "  Hand ID: " + str(hand.id) + "  Palm Position: " + str(hand.palm_position)
                #        normal = hand.palm_normal  # Normal Vector
                #        direction = hand.direction  # Direction Vector
                #      print "direction:  " + str(direction)
                        # Pitch is the angle between the negative z-axis and the projection of the vector onto the y-z plane
                        #  Roll is the angle between the y-axis and the projection of the vector onto the x-y plane
                        #  Yaw is the angle between the negative z-axis and the projection of the vector onto the x-z plane
                #  timestamp = frame.timestamp
                #  fps = frame.current_frames_per_second
                #    for finger in hand.fingers:
                #        print "Type: " + self.finger_names[finger.type()]
                #        for b in range(0, 4):
                #            bone = finger.bone(b)
                #            print"Bone: " + self.bone_names[bone.type] \
                #                + "  Direction" + str(bone.direction)
                for gesture in frame.gestures():
                    if gesture.type == Leap.Gesture.TYPE_SWIPE:
                        if self.state_names[gesture.state] == "STATE_START":
                            self.change_mode(self)
                            swipe = SwipeGesture(gesture)
                            #  print str(timestamp)
                            #  print str(fps)

                    if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
                        self.change_view_mode(self)

    #  def detach(self):
        #  self.controller.remove_listener(self.listener)


def main():
    listener = LeapMotionListener()
    controller = Leap.Controller()
    controller.add_listener(listener)
    #  listener.controller.add_listener(listener)

    print "Press enter to quit"
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass
    finally:
        #  listener.controller.remove_listener(listener)
        controller.remove_listener(listener)

if __name__ == "__main__":
    main()

