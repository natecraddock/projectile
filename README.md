# Projectile

### [Download Projectile](https://github.com/natecraddock/projectile/releases/download/v1.0/projectile.py)
Right-click and save link as a Python file. Then install `projectile.py` in Blender.

### Projectile features:
- **Trajectory Tracing:** Projectile draws trajectories for each object so you can get an idea of how the object will interact with the scene.
- **Hassle-Free Physics:** Projectile handles all the keyframing so all you have to do is set a speed and click a button! Much faster and more accurate than doing this manually.
- **Object Settings:** Each object has its own settings tied to it, so don't worry about making a mistake because you can always go back and change something!
- **Real-World Units:** Projectile will use the same units that are used in the .blend file, so you can use m/s or ft/s so you can truly know how fast your objects will be moving.

## Usage
Projectile is located in the Physics tab of the sidebar
- Click **Add Object as Emitter** to set an object as a Projectile object. The execute operator will be applied and an empty (emitter) will be created at the same location as the object.
- Click **Remove Object** with an active emitter to remove all instances.
- Set the **Velocity** component for each axis.
- **Number** is to set the number of instances. (Default is 1)
- **Lifetime** is to set the lifetime of the instances. 0 means the instances will not be destroyed.
- Then click **Execute**, then you can play the animation and see the results.

### Projectile Settings
- Choose a **Solver Quality** to increase the physics solver quality.
- **Draw Trajectories** Has options to draw all, selected, or no trajectories in the 3D View

## Blender 2.7x
Projectile can be downloaded [here](https://github.com/natecraddock/projectile/tree/blender27x) for Blender 2.7x
