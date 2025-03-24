# kupaldownloader
zkteco downloader

implement the ZKTeco downloader tool, we will create a Python script that connects to the ZKTeco device, downloads raw data, saves it as a JSON file, and uploads the data back to the device. 
name "kupaldownloader"
separate tabs
Connect to the ZKTeco Device: 
Use its IP address and port. 
Download Raw Data: Extract fingerprint templates and user IDs. 
Save as JSON: Convert the data to a structured JSON format. 
Upload Data Back: Send the JSON data back to another (or the same) ZKTeco device.

create an executable version of the KupalDownloader tool.
First, we'll update the main script to include a complete main() function
Add a GUI interface option for easier use
supports both GUI and CLI modes, making it more user-friendly

modify setup script to handle the missing modules and dependencies. update the build options to include only the necessary packages and ensure Windows runtime dependencies
