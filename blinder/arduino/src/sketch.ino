int control_pin = 12;
boolean control_mode = false;
unsigned long blind_at = 0;

void setup()
{
	Serial.begin(9600);
	pinMode(control_pin, OUTPUT);
	set_blind();
	Serial.println("pong");
	Serial.flush();

}

void set_blind() {
	digitalWrite(control_pin, LOW);
}

void set_unblind() {
	digitalWrite(control_pin, HIGH);
}

void lift_blinder() {
	if(blind_at != 0) {
		return;
	}

	set_unblind();
	blind_at = millis() + 300;
}

void handle_command(char command) {
	Serial.print("Handling command ");
	Serial.println(command);
	switch(command) {
		case 'b':
			Serial.println("Blind mode");
			Serial.flush();
			control_mode = false;
			set_blind();
			break;
		case 'u':
			Serial.println("Unblind mode");
			Serial.flush();
			control_mode = false;
			set_unblind();
			break;
		case 'c':
			Serial.println("Control mode");
			control_mode = true;
			set_blind();
			break;
		case 'l':
			if(control_mode) {
				Serial.println("Lifting");
				lift_blinder();
			}
			break;

		case 'p':
			Serial.println("pong");
			Serial.flush();
			break;

	}
	Serial.flush();

}

void serialEvent() {
	while(Serial.available()) {
		handle_command(Serial.read());
	}
}

void loop()
{
	if(control_mode && blind_at > 0) {
		if(millis() > blind_at) {
			blind_at = 0;
			set_blind();
		}
	}
}
