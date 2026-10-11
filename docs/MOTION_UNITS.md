# Motion coordinate convention

- Machine origin after homing: X=0, Y=0, Z=0.
- Working machine coordinates are non-negative: 0..Max for each axis.
- The motor still needs to move in both physical directions. "Positive coordinates only" does not mean disabling reverse motion.
- HMI stores and displays positions in **mm**.
- PLC Motion Technology Object converts engineering units to PTO pulses using mechanics configuration.

For PTO axes configure in TIA Portal:

- Pulses per motor revolution.
- Load motion / distance per motor revolution.
- Linear axis unit = mm.
- Software limits in mm.
- Homing direction and reference switch.

If a Technology Object is not used, keep one conversion block in PLC:

`pulse_per_mm = pulses_per_motor_rev / distance_per_motor_rev_mm`

and do not spread pulse values through the HMI/config files.
