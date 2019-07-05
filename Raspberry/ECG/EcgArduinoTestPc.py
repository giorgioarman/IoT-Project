import serial



if __name__ == '__main__':

    arduino = serial.Serial('COM7', 9600, timeout=.1)
    while True:
        arduinoData = arduino.readline()
        if arduinoData:
            print arduinoData.rstrip('\n')
