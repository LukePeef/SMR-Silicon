#define LEDPIN 4  // LED indicator

// Define sensor pins in an array
const int SENSOR_PINS[] = {2, 4, 5, 6};
const int NUM_SENSORS = sizeof(SENSOR_PINS) / sizeof(SENSOR_PINS[0]);
int count = 0;

// Variables to track sensor states
int sensorStates[NUM_SENSORS] = {0};
int lastStates[NUM_SENSORS] = {0};

void setup() {
  pinMode(LEDPIN, OUTPUT);  // LED as output

  // Initialize sensor pins as inputs with internal pull-ups
  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(SENSOR_PINS[i], INPUT_PULLUP);
  }

  Serial.begin(9600);
  Serial.println("Sensor Monitoring Started...");
}

void loop() {
  bool anySensorBroken = false;

  for (int i = 0; i < NUM_SENSORS; i++) {
    sensorStates[i] = digitalRead(SENSOR_PINS[i]);

    if (sensorStates[i] != lastStates[i]) {  // Detect state change
      Serial.print("\nSensor ");
      Serial.print(i + 1);
      Serial.print(": ");
      Serial.println(sensorStates[i] ? "Unbroken" : "Broken");

      if (!sensorStates[i]) {
        anySensorBroken = true;  // If any sensor is broken, set flag
        count++;
      }
    }

    lastStates[i] = sensorStates[i];  // Update last state
  }

  // Turn LED on if any sensor is broken, off otherwise
  //digitalWrite(LEDPIN, anySensorBroken ? HIGH : LOW);
  
 // delay(10);  // Small delay to reduce noise
}
