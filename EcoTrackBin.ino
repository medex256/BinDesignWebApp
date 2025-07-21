#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// similar to c++ syntax
// --------------------------
// Configuration Parameters
// --------------------------

const char *ssid = "Madi";          // Wi-Fi SSID
const char *password = "*********"; //

// Server address
const char *serverName = "http://34.96.175.5";

// ESP32's associated Bin ID
const int binId = 1; // BinId==1 for our demo

// Servo setup
Servo myservo;          // Create servo object
const int servoPin = 5; // GPIO pin for the servo

// Ultrasonic sensor pins
const int trigPin = 13;
const int echoPin = 12;

// OLED display settings
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1 // Use -1 if no reset pin
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Variables for ultrasonic sensor
long duration;
float distance;
float previousDistance = 10.0;
int trashCount = 0;

// Variables for session management
int sessionId = -1;           // Current session ID
const int invalidSession = 0; // Represents no active session
bool isBinFull = false;       // binFull status
String username = "";

// Timing variables
unsigned long lastSessionCheck = 0;
const unsigned long sessionCheckInterval = 2000; // Check every 2 seconds

// --------------------------
// Variables for Debounce Logic
// --------------------------
bool item_detected = false;               // Flag to indicate if an item has been detected
unsigned long last_count_time = 0;        // Timestamp of the last counted item
const unsigned long debounce_delay = 800; // 0.8 second cooldown

// --------------------------
// Variables for Non-blocking Bin Full Check
// --------------------------
bool checkingBinFull = false;
unsigned long binCheckStartTime = 0;

// --------------------------
// Setup Function
// --------------------------
void setup()
{
    Serial.begin(115200);

    // Attach the servo
    myservo.attach(servoPin);

    // Set up ultrasonic sensor pins
    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);

    // Initialize OLED display
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
    { // Address 0x3C for 128x64
        Serial.println("SSD1306 allocation failed");
        for (;;)
            ; // Don't proceed, loop forever
    }
    display.clearDisplay();
    display.display();

    // Connect to Wi-Fi
    connectToWiFi();

    // Initial display update
    updateDisplay();
}

// --------------------------
// Main Loop Function
// --------------------------
void loop()
{
    unsigned long currentMillis = millis();

    // Check for active session ID at intervals
    if (currentMillis - lastSessionCheck >= sessionCheckInterval)
    {
        lastSessionCheck = currentMillis;
        int previousSessionId = sessionId; // Store the current session ID as int

        // Check bin status before starting a new session
        if (sessionId == invalidSession)
        {
            // Get bin full status from server
            isBinFull = getBinFullStatus(); // websockets -> for the lid opening and closing -> "critical" in this projects ->
            updateDisplay();

            if (isBinFull)
            {
                Serial.println("Bin is full. Cannot start a new session.");
            }
            else
            {
                // Check for active session
                getActiveSessionId(); // Update sessionId

                // If session has just started
                if (previousSessionId == invalidSession && sessionId != invalidSession)
                {
                    // Start of session detected
                    openLid();
                    trashCount = 0; // Reset trash count
                    Serial.println("Session started. Lid opened.");
                    updateDisplay(); // Update display with welcome message
                }
            }
        }
        else
        {
            // If session is active, check if it has ended
            getActiveSessionId(); // Update sessionId

            // If session has just ended
            if (previousSessionId != invalidSession && sessionId == invalidSession)
            {
                // End of session detected
                closeLid();
                Serial.println("Session ended. Lid closed.");

                // Send trash count to the server using the valid session ID
                sendTrashCount(previousSessionId);

                // Start bin full check
                checkingBinFull = true;
                binCheckStartTime = currentMillis;

                // Reset trash count and username
                trashCount = 0;
                username = "";
            }
        }
    }

    if (checkingBinFull)
    {
        unsigned long elapsed = millis() - binCheckStartTime;
        if (elapsed < 5000)
        { // Check for 5 seconds
            measureDistance();
            if (distance >= 5.0)
            {                      // 5cm for not full
                isBinFull = false; // Bin is not full
                Serial.println("Bin is not full after session.");
                checkingBinFull = false;
                sendBinFullStatus(); // Send updated status to server
                updateDisplay();     // Update display with bin status
            }
        }
        else
        {
            isBinFull = true;
            Serial.println("Bin is full after session.");
            checkingBinFull = false;
            sendBinFullStatus(); // send updated status to server
            updateDisplay();     // update display with bin status
        }
    }

    // if a session is active start counting logic, measure distance and count items
    if (sessionId != invalidSession)
    {
        // Measure distance using ultrasonic sensor
        measureDistance();

        // Debounce Logic to Prevent Multiple Counts for the Same Item
        if (distance < 7.0 && !item_detected)
        {
            unsigned long currentTime = millis();

            // Check if enough time has passed since the last count
            if (currentTime - last_count_time >= debounce_delay)
            {
                trashCount++;
                Serial.print("Item detected. Trash count: ");
                Serial.println(trashCount);
                updateDisplay(); // Update display with new trash count

                // Update flags and timestamp
                item_detected = true;
                last_count_time = currentTime;
            }
        }

        // Reset the detection flag when the item moves away
        if (distance >= 7.0 && item_detected)
        {
            item_detected = false;
        }

        previousDistance = distance;
    }

    delay(10); // 10 ms = 0.01s 100ms = 0.1s
}

// --------------------------
// Function to Connect to Wi-Fi
// --------------------------
void connectToWiFi()
{
    Serial.print("Connecting to ");
    Serial.println(ssid);

    WiFi.begin(ssid, password);

    int retryCount = 0;
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(1000);
        Serial.print(".");
        retryCount++;
        if (retryCount > 30)
        { // Timeout after ~30 seconds
            Serial.println("\nFailed to connect to Wi-Fi.");
            return;
        }
    }

    Serial.println("\nConnected to Wi-Fi");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
}

// --------------------------
// Function to Measure Distance
// --------------------------
void measureDistance()
{
    // Trigger the ultrasonic sensor
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    // Read the echo pin
    duration = pulseIn(echoPin, HIGH, 30000); // Timeout after 30ms
    if (duration == 0)
    {
        distance = 999; // No echo received
    }
    else
    {
        distance = duration * 0.034 / 2; // Calculate distance in cm
    }

    // Serial.print("Distance: ");
    // Serial.print(distance);
    // Serial.println(" cm");
}

// --------------------------
// Function to Get Active Session ID
// --------------------------
void getActiveSessionId()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;
        String url = String(serverName) + "/get_active_session?bin_id=" + String(binId);
        http.begin(url);

        http.addHeader("Content-Type", "application/json");

        int httpResponseCode = http.GET();

        if (httpResponseCode == 200)
        {
            String response = http.getString();

            // parse JSON response
            DynamicJsonDocument doc(1024);
            DeserializationError error = deserializeJson(doc, response);

            if (!error)
            {
                if (doc["status"] == "success")
                {
                    sessionId = doc["session_id"].as<int>();
                    username = doc["username"].as<String>();
                    Serial.print("Active Session ID: ");
                    Serial.println(sessionId);
                    Serial.print("Username: ");
                    Serial.println(username);
                }
                else
                {
                    sessionId = invalidSession;
                    username = "";
                    Serial.println("No active session.");
                }
            }
            else
            {
                Serial.print("JSON parse error: ");
                Serial.println(error.f_str());
                sessionId = invalidSession;
                username = "";
            }
        }
        else
        {
            sessionId = invalidSession;
            username = "";
            Serial.print("GET request failed, error code: ");
            Serial.println(httpResponseCode);
        }

        http.end();
    }
}

// --------------------------
// Function to Get Bin Full Status from Server
// --------------------------
bool getBinFullStatus()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;
        String url = String(serverName) + "/get_bin_status?bin_id=" + String(binId);
        http.begin(url);

        http.addHeader("Content-Type", "application/json");

        int httpResponseCode = http.GET();

        if (httpResponseCode == 200)
        {
            String response = http.getString();

            // parse JSON response
            DynamicJsonDocument doc(512);
            DeserializationError error = deserializeJson(doc, response);

            if (!error)
            {
                bool binFull = doc["bin_full"].as<bool>();
                Serial.print("Bin full status from server: ");
                Serial.println(binFull);
                return binFull;
            }
            else
            {
                Serial.print("JSON parse error: ");
                Serial.println(error.f_str());
                return true; // bin is full in case of error ->do not open the lid
            }
        }
        else
        {
            Serial.print("GET request failed, error code: ");
            Serial.println(httpResponseCode);
            return true; // bin is full in case of error ->do not open the lid
        }

        http.end();
    }
    return true; // bin is full in case of error ->do not open the lid
}

// --------------------------
// Function to Send Bin Full Status to Server
// --------------------------
void sendBinFullStatus()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;
        String url = String(serverName) + "/update_bin_status";
        http.begin(url);

        http.addHeader("Content-Type", "application/json");

        // Create JSON payload
        DynamicJsonDocument doc(512);
        doc["bin_id"] = binId;
        doc["binFull"] = isBinFull;

        String postData;
        serializeJson(doc, postData);

        int httpResponseCode = http.POST(postData);

        if (httpResponseCode > 0)
        {
            String response = http.getString();
            Serial.print("HTTP Response code: ");
            Serial.println(httpResponseCode);
            Serial.println("Response: " + response);
        }
        else
        {
            Serial.print("Error on sending POST: ");
            Serial.println(httpResponseCode);
        }

        http.end();
    }
    else
    {
        Serial.println("Cannot send bin full status. Not connected to Wi-Fi.");
    }
}

// --------------------------
// Function to Send Trash Count
// --------------------------
void sendTrashCount(int session_id)
{
    if (WiFi.status() == WL_CONNECTED && session_id != invalidSession)
    {
        HTTPClient http;
        String url = String(serverName) + "/update_trash_count";
        http.begin(url);

        http.addHeader("Content-Type", "application/json");

        // Create JSON payload
        DynamicJsonDocument doc(1024);
        doc["session_id"] = session_id;
        doc["trash_count"] = trashCount;

        String postData;
        serializeJson(doc, postData);

        int httpResponseCode = http.POST(postData);

        if (httpResponseCode > 0)
        {
            String response = http.getString();
            Serial.print("HTTP Response code: ");
            Serial.println(httpResponseCode);
            Serial.println("Response: " + response);
        }
        else
        {
            Serial.print("Error on sending POST: ");
            Serial.println(httpResponseCode);
        }

        http.end();
    }
    else
    {
        Serial.println("Cannot send trash count. No active session.");
    }
}

// --------------------------
// Function to Open Lid
// --------------------------
void openLid()
{
    Serial.println("Opening lid...");
    myservo.write(135); // Rotate to open position
    delay(700);         // Hold for 0.5 seconds
    myservo.write(90);  // Return to neutral position
    Serial.println("Lid opened.");
}

// --------------------------
// Function to Close Lid
// --------------------------
void closeLid()
{
    Serial.println("Closing lid...");
    myservo.write(45); // Rotate to close position
    delay(500);        // Hold for 0.5 seconds
    myservo.write(90); // Return to neutral position
    Serial.println("Lid closed.");
}

// --------------------------
// Function to Update OLED Display
// --------------------------
void updateDisplay()
{
    display.clearDisplay();
    display.setTextColor(WHITE);
    display.setCursor(0, 0);

    if (isBinFull)
    {
        display.setTextSize(2);
        display.println("Bin");
        display.println("is full!");
    }
    else if (sessionId != invalidSession)
    {
        display.setTextSize(2);
        display.println("Hello");
        display.println(username);
        display.println("Count: " + String(trashCount));
    }
    else
    {
        display.setTextSize(2);
        display.println("Waiting");
        display.println("for");
        display.println("session...");
    }

    display.display();
}