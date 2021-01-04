volatile int IRQcount;
int pin = 2;
int pin_irq = 0; //IRQ that matches to pin 2 for UNO.  Numbers match for NanoEvery
int pulsesPerSecond = 0; //pulses per second
unsigned long serial = 1;  //Serial to keep track of data segments in batch
int cycle = 0; //toggle to 1 for the start of a new blockTime
int blockTimer = 0; //Used to track the block time in seconds
int blockTime = 60; //block time in seconds
unsigned long pulseCount = 0; //Number of pulses for last time block
unsigned long pulseCount2 = 0;
float voltage = 0; //House leg-leg voltage reading ~240V
float pumpCurrent = 0;  //Water Pump Input Current
float pumpCurrentResistor = 99.4; //actual resistance value
float voltageSeriesResistor = 99900;
float voltageSenseResistor = 994;
float voltageDivider = voltageSenseResistor/(voltageSenseResistor+voltageSeriesResistor);
int period = 1000; //1000ms period of sampling
int frequency = 60; 
int samples = 112; //Number of samples to find peak pump current


void setup() {
//Serial is USB only on Arduino Nano Every, Serial1 is the pin TX1/RX0
Serial1.begin (2400);
pinMode(pin,INPUT);
pinMode(A0,INPUT);
pinMode(A1,INPUT);
attachInterrupt(pin, IRQcounter, RISING);
}

void IRQcounter(){
  IRQcount++;
}

void countReset(){
  blockTimer = 0;
  cycle =1;
  pulseCount2 = pulseCount;
  pulseCount = 0;
}

float get_max(char aPin[]){
  float maxV = 0;
  float read = 0;
  for(int i=0; i<samples; i++){
    read = analogRead(aPin);
    if(maxV < read) maxV=read;
    delayMicroseconds(1/(frequency*samples));
  }
  return maxV;
}

void loop() {

if(millis()%period == 0){
  cli(); //disable interrupts
  pulsesPerSecond = IRQcount;
  IRQcount = 0;
  sei(); //enable interrupts
 
  pulseCount = pulseCount + pulsesPerSecond;

 //20[A/V]*V, 5/1023 for ADC
pumpCurrent = get_max(A1)*20*5/1023/sqrt(2)*(pumpCurrentResistor/100);

//Vsense = voltageDivider* ACinput, 5/1023 for ADC
//voltage = analogRead(A0)/voltageDivider*(5/1023);

voltage = get_max(A0)/voltageDivider*5/1023;

// Use Serial for USB or Arudino UNO
  Serial1.print(",");
  Serial1.print(serial);
  Serial1.print(",");
  Serial1.print(blockTime);
  Serial1.print(",");
  Serial1.print(cycle);
  Serial1.print(",");
  Serial1.print(pulsesPerSecond);
  Serial1.print(",");
  Serial1.print(pulseCount2);
  Serial1.print(",");
  Serial1.print(pumpCurrent);
  Serial1.print(",");
  Serial1.print(voltage);
  Serial1.println(",");
  
  if (cycle==1){
    pulseCount2 = 0;
  }
  serial++;
  blockTimer++;
  cycle = 0;
  pumpCurrent = 0;
  
  if (blockTimer >= blockTime){
    countReset();
  }
}

}
