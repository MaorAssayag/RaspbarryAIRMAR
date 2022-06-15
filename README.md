# Raspbarry AIRMAR
![alt tag](https://github.com/MaorAssayag/RaspbarryAIRMAR/blob/main/dashboard.jpg)
 Raspbarry pi 4 parsing NMEA2000 senteces from AIRMAR-WX150 and publishing the data with Prometheus remote-write.
 Weather metrics are beeing displayed in Grafana Cloud dashboard
 
 ## Entities 
* Raspbarry pi 4
* AIRMAR WX150
* SIMRAD
* Grafana Cloud

*Raspbarry pi 4* connected to SIMRAD over wifi
## Flow
* AIRMAR WX150 Serial communication to SIMRAD
* SIMRAD TCP SERVER over internal wifi
* RASPBARRY Pi 4 
  * Python 3.7 service : TCP CLIENT over wifi & NMEA2000 parsing + prometheus metrics client
  * Prometheus remote-write
* Grafana cloud displaying dashboard from cloud prometheus agent

