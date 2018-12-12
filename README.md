# Projectile

### [Download Projectile](https://raw.githubusercontent.com/natecraddock/projectile/master/projectile.py)

### Projectile features:
- **Trajectory Tracing:** Projectile draws trajectories for each object so you can get an idea of how the object will interact with the scene.
- **Hassle-Free Physics:** Projectile handles all the keyframing so all you have to do is set a speed and click a button! Much faster and more accurate than doing this manually.
- **Object Settings:** Each object has its own settings tied to it, so don't worry about making a mistake because you can always go back and change something!
- **Real-World Units:** Projectile will use the same units that are used in the .blend file, so you can use m/s or ft/s so you can truly know how fast your objects will be moving.

## Usage
- Click **Add Object** to set an object as a Projectile object. It will set it to be an active rigidbody object, and will set the **Initial Location** and **Initial Rotation** based on any transforms the object has.
- Click **Remove Object** to remove an object from projectile calculations.
  - *Both **Add Object** and **Remove Object** support multiple objects in selection.*
- Set the **Initial Location** by changing the location sliders.
- Set the **Velocity** component for each axis.
- Then click **Launch!**, then you can play the animation and see the results. (Launch is only available if **Auto Update** is not checked.)

### Projectile Settings
- Choose a **Solver Quality** to increase the physics solver quality.
- Check **Auto Update** for the trajectory calculations to happen after each property update.
- Check **Auto Play** to automatically start the animation player after each trajectory calculation
- Check **Draw Trajectories** To draw trajectories in the 3D View for the active object. Trajectories are terminated at the end of the timeline, or if a collision is detected in the path.

## Blender 2.7x
Projectile can be downloaded [here](https://github.com/natecraddock/projectile/tree/blender27x) for Blender 2.7x
