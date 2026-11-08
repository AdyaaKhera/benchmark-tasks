# Set up a culture tray for three samples

A task file for the `yam_arena` embodiment ([yam-isaac-lab-arena](https://github.com/kairosiann/yam-isaac-lab-arena),
Isaac Lab-Arena 0.3.1) on the station scene: [culture_tray_setup.py](culture_tray_setup.py).

The instruction is only "Set up the tray for culturing three samples." The robot has to work out the rest from the
scene: three tubes (not all four clean ones) into the rack, the Petri dish onto the circle printed for it, the syringe
onto its strip. Nothing in the instruction says to leave out the tube of cloudy old culture or the syringe already
full of red fluid. Putting either in the rack or tray, even for a moment, scores 0.

## Run a trial

On a machine set up with the official simulator (the Robocurve Brev launchable), with a Dream API key in
`~/.dreamlabs/credentials`, from this folder:

```bash
# Dream-1
inspect-robots run --embodiment yam_arena --policy dream \
  -E task=culture_tray_setup.py -E object_jitter=0 -E control_hz=20 -E cam_width=320 -E cam_height=176 \
  --instruction "Set up the tray for culturing three samples." \
  --scorer task_score --max-steps 2400 --store-frames --log-dir ~/yam-eval/culture-tray-dream

# The scripted demo, which reaches full score
inspect-robots run --embodiment yam_arena --policy yam_scripted \
  -E task=culture_tray_setup.py -E object_jitter=0 -E control_hz=20 -E cam_width=320 -E cam_height=176 \
  --instruction "Set up the tray for culturing three samples." \
  --scorer task_score --max-steps 2400 --store-frames --log-dir ~/yam-eval/culture-tray-demo

# One MP4 per camera, next to each run's frames
for log in ~/yam-eval/culture-tray-*/*.json; do inspect-robots video "$log"; done
```

The run prints `task_score` at the end. The trial ends with 1.0 once `success()` has held for 1 s; otherwise it
scores `score()` at the last step.

## Scoring

| Score | Condition | Check on a real table |
|---|---|---|
| 0 | the yellow tube or the red syringe was ever set in the rack or down in the tray, even if taken out again | watch the trial |
| +0.2 each, up to 3 | a clear tube standing in a rack pocket: bottom on the pocket floor (within 5 mm), leaning at most 18 degrees | a top photo |
| 0 for tubes | four clear tubes racked: the instruction asks for three samples | a top photo |
| +0.2 | the dish flat on the circle, centre within 15 mm of the circle's centre | a ruler |
| +0.2 | the empty syringe flat on the strip, centre within 3 cm along and 1.5 cm across it, turned at most 20 degrees | a ruler |

Possible scores: 0, 0.2, 0.4, 0.6, 0.8, 1.0. Which pockets hold the tubes doesn't matter.

- **Violations stick.** The scorer remembers a used item set in the rack or tray for the rest of the trial. It
  forgets only when every loose object is back within 1 cm of its start, as after a reset, where the score is 0
  anyway.
- **Poses, not grippers.** The scorer reads object poses, so a tube held motionless on a pocket floor counts. On a
  real table, open the grippers before the photo.
- **Centres and axes, not bounding boxes.** Arena builds an object's bounding box from its local box's corners, which
  swing out when a cylinder spins on its axis.

## The demo

`demo()` in the task file, open loop and deterministic. The right arm sets the dish on its circle and the empty
syringe on its strip, then parks over its own side. At the same time the left arm racks three clear tubes, skipping
the yellow one: far left pocket, then near left, then near right. Over the rack it opens its fingers only to 44 mm:
fully open, one finger would come down on the tube in the next pocket. It leaves the far right pocket empty, where the
left arm is near the edge of its reach.

## Runtime and seeds

- Scripted demo: TBD steps on an L40S.
- Dream-1: 2,400 steps (2 minutes simulated), TBD minutes on an L40S.
- `-E object_jitter=0` keeps the layout fixed, so no seed is needed.

## Tests

`python -m pytest -q test_culture_tray_setup.py` checks the scoring on hand-built states and replays both arms' demo
plans through the kinematics at 20 Hz (IK error under 0.5 mm), without the simulator. It needs `yam_arena`.
