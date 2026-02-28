I'm hacking together an integration between my Alarm and Home Assistant. 
This is a personal project as a learning exercise (although with a practical outcome).

If you're wanting a more proffesional integration have a look at https://github.com/thanoskas/arrowhead_alarm. 

I'm connecting to the a serial module on my alarm through a serial device server. 

Currently the integration is deployed and working. Further work can be done, but will likely be delayed until a need develops or other projects are complete. 

1. Commenting is a little lacking overall. 
2. Error handling for errors received from Alarm is nil. Definitely needs doing if deployed to any other systems. 
3. Investigate different methods of handling Zone Bypassing and recording timestamps in HA of when this happens. 


