# B[U]ILT Air Canvas Wand (Controller)

## Our Tech Stack

 Our current tech stack includes the use of:

 1. Python
 2. Raspberry Pis

## Best Practices

 To ensure our repository has less conflicts and to ensure everyone can develop fluidly we will implement best practices on branching, code reviews, descriptive naming/messages, modular reusable code, and commits.

 Please read up on these best practices as well, [What are Git version control best practices?](https://about.gitlab.com/topics/version-control/version-control-best-practices/)

### Branching

 Feature branching is a great way for teams to split up work and ensure there are reduced merge conflicts. This also ensures that the scope of pull requests are focused and specific. 

 A branch should be named with a proper name as well to signal to others what the purpose of the banch is, who is working on the branch, and where a feature will be located. 

 For example a branch for a rotating photo carousel feature on an about page by Steven can take on the form:  ***stevenuru/about/rotating-carousel***

### Commits

 Commits to a branch should be done granularly with frequency. Commiting large changes to a codebase can make it difficult for reviewers to gather a sense of what's going on and can make it more difficult to spot errors in one's code merge.

 Branch merges to main should also be reviewed by another committee member to reduce the risk of errors and to maintain a clean codebase.

### Writing Code

 #### Modularity
 
 Code should be written with reusability and modularity in mind. Functions should be used when possible to decrease repetititve code and makes it easier for reviewers to read when done right. Files should also be split up based on the functionality/purpose of the file. 

 #### Comments

 Comments should be used when the code itself cannot communicate to others what is happening. We should strive to use descriptive (although short) comments when defining new functions. This helps ramp up learning whenever someone new is introduced to the codebase

 # Getting Started
 
## Hardware
Hardware required for this project includes **2 Adafruit BNO08X IMUs** and **1 Raspberry Pi Zero 2 W**.  
The BNO085 can be purchased on Adafruit or Digi-Key: https://www.adafruit.com/product/4754  
The Raspberry Pi Zero 2 W can be purchased from official Raspberry Pi vendors: https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/  
  
### Setting up the Raspberry Pi
  
The OS we will use is **Raspberry Pi OS Lite (64-bit)** in order to save RAM and CPU resources. This can be installed via Raspberry Pi Imager. Devices should be named `built_X`, where X increments based on the number of Pis already registered in the BUILT_uiuc organization.  
   
![image](https://github.com/user-attachments/assets/b72cb3d4-7b25-4936-9b8f-1108849fd6a0)
Select the Raspberry Pi model you are using. For this project, this will be the Pi Zero 2 W.

![image](https://github.com/user-attachments/assets/f82765c7-f807-4e0b-95f3-b6f7144290c9)
Next, select Raspberry Pi OS Lite (64-bit), or another OS if you are not using a Raspberry Pi Zero 2 W.

![image](https://github.com/user-attachments/assets/59e5c9f8-2e94-42b5-b5de-bc62d3f73d3f)
Select the storage device that the Raspberry Pi will use.

![image](https://github.com/user-attachments/assets/88c8624b-0b1d-49ec-a2d4-a71462222841)
Choose a unique device name, preferably following the next sequence of built-eoh devices.

![image](https://github.com/user-attachments/assets/04c6f893-3f69-41ef-bbbc-3eb312b1cc27)
Select the localization settings for the US.

![image](https://github.com/user-attachments/assets/0d1bc40e-1561-4840-b927-0773709e4ef7)
Choose a username and password matching the device name, and use the default BUILT password.

![image](https://github.com/user-attachments/assets/f282401f-2793-4673-8251-4519b7feb924)
Add a public or private network. If the device will be connected to IllinoisNet, it must be added to the network whitelist: https://clearpasspub.techservices.illinois.edu/guest/auth_login.php  

![image](https://github.com/user-attachments/assets/c043a47a-f2c4-469f-a742-25578d7d365a)
Enable SSH with password authentication.

![image](https://github.com/user-attachments/assets/8902ca61-0f6f-4738-98dd-fb1093397faa)
Enable Raspberry Pi Connect and add it to the `built_uiuc` organization.

![image](https://github.com/user-attachments/assets/53c63be9-9f09-4a8a-9a5c-983dbda0f5c7)
Finally, write the image to the storage device.

Once the OS has been written, it is ready to plug into your device and begin software setup.

# Software

## Software Setup
To use CircuitPython on the Pi Zero, install Adafruit’s Blinka. Follow Adafruit’s guide and make sure to run the test:

https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi

With Blinka installed, you are ready to begin writing software. Note you must be in the virtual enviroment to write code. 
