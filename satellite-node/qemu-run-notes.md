# QEMU Run Notes (Concept)

In this prototype the satellite node runs directly as a Docker container
based on a Python image. For a more realistic embedded setup you can run
`sat_agentd.py` inside an ARM Linux root filesystem under QEMU.

A possible approach:

1. Build a minimal ARM rootfs with:
   - BusyBox
   - Python 3.x
   - `sat_agentd.py` and `orbit_model.py`

2. Use `qemu-system-arm` with a suitable machine type and kernel, for example:
   ```bash
   qemu-system-arm \
     -M virt \
     -kernel zImage \
     -append "root=/dev/vda console=ttyAMA0" \
     -drive if=none,file=rootfs.ext4,format=raw,id=hd \
     -device virtio-blk-device,drive=hd \
     -netdev user,id=net0,hostfwd=tcp::10022-:22,hostfwd=tcp::18000-:8000 \
     -device virtio-net-device,netdev=net0 \
     -nographic
   ```

3. Ensure that the QEMU guest can reach the ground-station API on the host
   (e.g. via user-mode networking and host port forwarding).

4. Inside the guest, run:
   ```bash
   export GROUNDSTATION_URL="http://10.0.2.2:8000"
   export SATELLITE_ID="SAT-001"
   export HMAC_SECRET="changeme"
   python3 /opt/satellite-node/sat_agentd.py
   ```

These steps are intentionally high-level so that the focus of this
repository stays on architecture and information-security aspects, while
still demonstrating familiarity with QEMU-based testing.
