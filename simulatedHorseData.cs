// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

// This application uses the Azure IoT Hub device SDK for .NET
// For samples see: https://github.com/Azure/azure-iot-sdk-csharp/tree/master/iothub/device/samples

using System;
using Microsoft.Azure.Devices.Client;
using Newtonsoft.Json;
using System.Text;
using System.Threading.Tasks;

namespace simulated_device
{
    class SimulatedDevice
    {
        private static DeviceClient s_deviceClient;

        // The device connection string to authenticate the device with your IoT hub.
        // Using the Azure CLI:
        // az iot hub device-identity connection-string show --hub-name {YourIoTHubName} --device-id MyDotnetDevice --output table
        private readonly static string s_connectionString = "HostName=myIoTHobTutorial.azure-devices.net;DeviceId=MyDotnetDevice;SharedAccessKey=vJKqjKZPztU+E4xfawc4/UuYgw6X6i03qXsGOSEWBEE=";

        private static int s_telemetryInterval = 1; // Seconds

        // Handle the direct method call
        private static Task<MethodResponse> SetTelemetryInterval(MethodRequest methodRequest, object userContext)
        {
            var data = Encoding.UTF8.GetString(methodRequest.Data);

            // Check the payload is a single integer value
            if (Int32.TryParse(data, out s_telemetryInterval))
            {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("Telemetry interval set to {0} seconds", data);
                Console.ResetColor();

                // Acknowlege the direct method call with a 200 success message
                string result = "{\"result\":\"Executed direct method: " + methodRequest.Name + "\"}";
                return Task.FromResult(new MethodResponse(Encoding.UTF8.GetBytes(result), 200));
            }
            else
            {
                // Acknowlege the direct method call with a 400 error message
                string result = "{\"result\":\"Invalid parameter\"}";
                return Task.FromResult(new MethodResponse(Encoding.UTF8.GetBytes(result), 400));
            }
        }

        // Async method to send simulated telemetry
        private static async void SendDeviceToCloudMessagesAsync()
        {

            Random rand = new Random();

            while (true)
            {
                double currentHR = 40 + rand.NextDouble() * 120; // 40 to 160 bpm
                double currentSpO2 = 90 + rand.NextDouble() * 10; // 90 to 100%
                double currentTemperature = 36 + rand.NextDouble() * 4; // 36 to 40°C

                var telemetryDataPoint = new
                {
                    horseId = "Horse001",
                    hr = Math.Round(currentHR, 1),
                    spo2 = Math.Round(currentSpO2, 1),
                    temperature = Math.Round(currentTemperature, 1)
                };

                var messageString = JsonConvert.SerializeObject(telemetryDataPoint);
                var message = new Message(Encoding.ASCII.GetBytes(messageString));

                // Add a custom application property to the message.
                // An IoT hub can filter on these properties without access to the message body.
                message.Properties.Add("temperatureAlert", (currentTemperature > 30) ? "true" : "false");

                // Send the telemetry message
                await s_deviceClient.SendEventAsync(message);
                Console.WriteLine("{0} > Sending message: {1}", DateTime.Now, messageString);

                await Task.Delay(s_telemetryInterval * 1000);
            }
        }
        private static void Main(string[] args)
        {
            Console.WriteLine("IoT Hub Quickstarts #2 - Simulated device. Ctrl-C to exit.\n");

            // Connect to the IoT hub using the MQTT protocol
            s_deviceClient = DeviceClient.CreateFromConnectionString(s_connectionString, TransportType.Mqtt);

            // Create a handler for the direct method call
            s_deviceClient.SetMethodHandlerAsync("SetTelemetryInterval", SetTelemetryInterval, null).Wait();
            SendDeviceToCloudMessagesAsync();
            Console.ReadLine();
        }
    }
}
