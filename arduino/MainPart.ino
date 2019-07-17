/*!
IoT for Health
Barrese Venere Sabrina 245877
Ebrahimi Mehr Iman 250190
Odasso Giorgia 244158
Steno Lorenzo 253605
 */


#include "HeartSpeed.h"

// Create an instance of heart speed class, the parameter is number of pin that we connected EDG to Arduino
HeartSpeed heartspeed(A1);  


void setup() {
  // set the baud rate of TCP connection
  Serial.begin(9600);

  heartspeed.setCB(mycb);    

  heartspeed.begin();
}

void loop() {

}

// definition function to read the data from the pin and pass to the HeartSpeed class
void mycb(uint8_t rawData, int value)
{
  if(rawData){
    Serial.println(value);
  }else{
    Serial.print("HeartRate Value = "); Serial.println(value);
  }
}
