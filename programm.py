#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor,  ColorSensor, UltrasonicSensor)
from pybricks.parameters import Port, Direction, Button
from pybricks.tools import StopWatch
from pybricks.robotics import DriveBase

import math

# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.


# Alle Objekte kreeiren zur Steuerung des Roboters
ev3 = EV3Brick()
motor_left = Motor(Port.A)
motor_right = Motor(Port.B)
ultra_motor = Motor(Port.C, Direction.COUNTERCLOCKWISE) # Motor für die Rotation des Ultraschallsensors

ultra_sensor = UltrasonicSensor(Port.S1)
cs_right = ColorSensor(Port.S2)
cs_left = ColorSensor(Port.S3)

robot = DriveBase(motor_left, motor_right, 56, 87)
robot.settings(300, 1000)

watch = StopWatch() # Stoppuhr für die Messung der Zeit

# Write your program here.
ev3.speaker.beep()
ultra_motor.reset_angle(0)  # Initiale Rotation des Ultraschallsensors als 0 definieren


# Alle Zustände
RAND_LINKS = 11
RAND_RECHTS = 12
FAHREN = 2
SCANNEN_RECHTS = 31
SCANNEN_LINKS = 32
NICHTS = 4

not_angle = 120  # Drehwinkel nach dem Erreichen des Randes
reflection_limit = 30  # Anteil des reflektierten Lichtes, zur Bestimmung ob der Rand erreicht wird

maxa_target = 90  # Maximaler Auslenkungswinkel des Ultraschallsensors
mina_target = -90  # Minimaler Auslenkungswinkel des Ultraschallsensors
us_speed = 90  # Die Winkelgeschwindigkeit des Ultraschallsensors
us_distances = {}  # Dictionary, zu jedem Winkel wird später ein Wert für die Distanz zugeteilt

drive_speed = 300  # Geschwindigkeit des Roboters in mm/s
turn_speed = 0  # Drehgeschwindigkeit des Roboters in °/s


# Als Erstes soll der Roboter nach rechts nach einem anderen Roboter scannen
zustand = SCANNEN_RECHTS
watch.reset()   # Hier beginnen die Zeit zu messen


def reflection_detection():
    """
    Prüft, ob der Roboter sich am Rand des Rings befindet
    Returns
    --------
    int or None
        Der neue Zustand, falls der Roboter sich am Rand befindet, sonst None
    """
    
    if cs_left.reflection() > reflection_limit: # Reflektion des rechten Farbsensors grösser als das Limit
        zustand = RAND_LINKS
    elif cs_right.reflection() > reflection_limit:  # Reflektion des linken Farbsensors grösser als das Limit
        zustand = RAND_RECHTS
    else:   # Beide Farbsensoren haben keine grosse Reflektio gefunden
        zustand = None
    return zustand

def check_end():
    """
    Testet, ob das Programm verlassen werden soll
    Returns
    -------
    int or None
        `NICHTS`falls das Programm verlassen wird, sonst None
    """
    
    # Wenn 90 Sekunden verstrichen sind oder die linke Taste des Roboters gedrückt wurde, wird das Programm verlassen
    if watch.time() > 90000 or Button.LEFT in ev3.buttons.pressed():
        ultra_motor.hold()  # Ultraschallsensor stoppen
        robot.stop()    # Roboter stoppen
        return NICHTS
    
    return None
    
# Zum Starten des Programms muss die rechte Taste des Roboters gedrückt werden
while not Button.RIGHT in ev3.buttons.pressed():
    pass

# Die Zeit wird hier angefangen zu zählen
watch.reset()


# Zustandsmaschine
while True:
    zustand = check_end() or zustand    # Zustand soll verändert werden falls das Programm verlassen werden soll

    # Der übliche Fahrzustand
    if zustand == FAHREN:
        ultra_motor.run_target(us_speed, 0, wait=False) # Ultraschallsensor wird auf die initiale Rotation gebracht
        robot.drive(drive_speed, turn_speed)    # Roboter fährt mit gewisser Geschwindigkeit

        zustand = reflection_detection() or zustand # Zustand ändert sich, falls der Roboter am Rand ist

        

    # Roboter ist auf der linken Seite am Rand
    elif zustand == RAND_LINKS:
        robot.turn(not_angle)   # Roboter soll sich um einen Winkel in Uhrzeigersinn drehen
        zustand = SCANNEN_RECHTS    # Zustand wechseln, um nach Gegnern zu scannen
        us_distances.clear()

    # Roboter ist auf der rechten Seite am Rand
    elif zustand == RAND_RECHTS:
        robot.turn(-not_angle)  # Roboter soll sich um einen Winkel in Gegenuhrzeigersinn drehen
        zustand = SCANNEN_RECHTS    # Zustand wechseln, um nach Gegnern zu scannen
        us_distances.clear()

    # Roboter scannt nach rechts für Gegner
    elif zustand == SCANNEN_RECHTS:
        ultra_motor.run(us_speed)   # Ultraschallsensormotor drehen lassen in Uhrzeigersinn
        us_distances[ultra_motor.angle()] = ultra_sensor.distance() # Den derzeitigen Richtungswinkel des Ultraschallsensors mit der gemessenen Distanz verbinden

        # Falls der Ultraschallsensor einen Winkel von 90° hat, in andere Richtung scannen
        if ultra_motor.angle() >= 90:
            zustand = SCANNEN_LINKS
        
        zustand = reflection_detection() or zustand # Zustand ändert sich, falls der Roboter am Rand ist


    # Roboter scannt nach links für Gegner
    elif zustand == SCANNEN_LINKS:
        ultra_motor.run(-us_speed)  # Ultraschallsensormotor drehen lassen in Gegenuhrzeigersinn
        us_distances[ultra_motor.angle()] = ultra_sensor.distance() # Den derzeitigen Richtungswinkel des Ultraschallsensors mit der gemessenen Distanz verbinden
 
        if ultra_motor.angle() <= -90:
            angle = min(us_distances, key=us_distances.get) # Winkel, bei der die kleinste Entfernung gemessen wurde
            ultra_motor.stop()  # Motor des Ultraschallsensors stoppen
            
            # Wenn der Gegner gerade vor uns ist, muss man nicht die Winkelgeschwindigkeit berechnen, sonder gerade auf 0 setzen. 
            if us_distances[angle] == 0:
                turn_speed = 0
            else:
                turn_speed = drive_speed * 360 * math.sin(angle) / (math.pi * us_distances[angle]) # Die Winkelgeschwindigkeit berechnen
                
            while not watch.time() > 5000:  # Nur fahren wenn schon 5 Sekunden verstrichen sind
                pass    
            zustand = FAHREN
        zustand = reflection_detection() or zustand # Zustand ändert sich, falls der Roboter am Rand ist

    # Das Programm verlassen
    elif zustand == NICHTS:
        ultra_motor.run_target(us_speed, 0) # Ultraschallsensor wird auf die initiale Rotation gebracht
        break   # Unendliche while-Schleife mit einem `break` verlassen
