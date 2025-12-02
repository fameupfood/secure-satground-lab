# Secure SatGround Lab

A small but realistic Linux/Docker/QEMU-style testbed that simulates a secure
satellite ground segment with a virtual satellite node, a ground-station API
and a security monitoring component.

The focus is on:

- Simplified **satellite modelling** (orbit & contact window)
- **Secure telemetry** (TLS-ready HTTP + HMAC signatures)
- **Secure command channel** (signed commands with sequence numbers)
- **IT architecture & security monitoring**
- A setup that can be extended to run the satellite node inside a QEMU/ARM
  virtual machine

## 1. Architecture

The lab consists of three main components:

1. `satellite-node`  
   A small Python daemon (`sat_agentd.py`) that simulates a satellite payload
   computer. It runs on Linux and can be containerised with Docker. The node

   - models a simple circular orbit in `orbit_model.py`
   - computes latitude / longitude / altitude as a function of time
   - derives a binary *contact window* flag (whether the ground station is in view)
   - sends JSON telemetry to the ground station during contact windows
   - attaches an HMAC-SHA256 signature to each telemetry frame

2. `groundstation-api`  
   A FastAPI-based REST backend that accepts telemetry and stores it in a
   small SQLite database. It also exposes a `/command` endpoint that can be
   used to simulate commands to the satellite.

   - `/telemetry` (POST): ingest telemetry frames, verify HMAC signature,
     store a row in `telemetry` table.
   - `/command` (POST): accept signed commands with a monotonically
     increasing sequence number (replay protection).
   - `/telemetry/latest` (GET): return the latest telemetry row for quick
     manual checks.
   - The shared HMAC secret is provided via the `HMAC_SECRET` environment
     variable.

3. `security-monitor`  
   A light-weight monitoring component that periodically reads the SQLite
   database and performs basic anomaly checks, for example:

   - sudden jumps in battery state-of-charge
   - impossible altitude values
   - unrealistic temperature steps

   Detected anomalies are printed to stdout as JSON alerts. This container
   demonstrates basic **security monitoring / analytics** for a
   satellite-ground link.

A PlantUML architecture diagram and a simple sequence diagram are stored in
`docs/architecture-diagram.puml` and `docs/sequence-diagram.puml`. Example
images (exported diagrams) are stored in the `docs/` directory as well.

## 2. Security Features (Informationssicherheit)

This lab demonstrates several information-security aspects relevant for a
satellite ground segment:

- **Transport security (TLS-ready)**  
  The HTTP communication between satellite node and ground station is
  prepared for TLS / mTLS. In this prototype, TLS termination can be added
  via a reverse proxy or by running the FastAPI app behind an HTTPS
  terminator (e.g. nginx, stunnel).

- **Application-level message authentication**  
  Each telemetry and command message carries an HMAC-SHA256 signature based
  on a shared secret (`HMAC_SECRET`). The ground station recomputes the
  HMAC and rejects messages with invalid signatures.

- **Replay protection for commands**  
  Commands include a `sequence_number`. The ground station can store the
  last accepted sequence number and reject commands with stale sequence
  values.

- **Role-based access (lightweight)**  
  The design allows for distinguishing read-only users (telemetry viewers)
  from operators who are allowed to send commands. In a real deployment,
  this would be integrated with an identity provider or API gateway.

- **Security monitoring & anomaly detection**  
  The separate `security-monitor` container demonstrates how telemetry
  data can be analysed for abnormal patterns. In a real Early Warning
  system (e.g. SBMD / ODIN's EYE context), more advanced statistical or
  ML-based methods could be applied on top of this basic pipeline.

## 3. Satellite Modelling (Satellitentechnik)

The satellite orbit is modelled as a simple circular orbit in `orbit_model.py`:

- configurable orbital period (e.g. 5400 s)
- inclination in degrees
- a fixed ground-station location (lat / lon)
- a distance threshold that defines when the satellite is "in view"

At runtime, the satellite node computes:

- latitude / longitude / altitude as function of wall-clock time
- a `contact_window` flag based on great-circle distance to the ground
  station

The `docs/orbit-groundtrack.png` image shows an example ground track of the
simulated satellite over multiple orbits. The battery time series in
`docs/telemetry-battery.png` illustrates how a spoofed telemetry frame
could create an unrealistic jump that the security monitor can detect.

This is, of course, a strong simplification compared to real mission
analysis, but it is sufficient to demonstrate familiarity with basic
concepts used in satellite-ground architectures.

## 4. Running the Lab with Docker

Requirements:

- Docker
- docker-compose

Build and start all services:

```bash
docker-compose up --build
```

This will start three containers:

- `groundstation-api` on port `8000`
- `satellite-node`
- `security-monitor`

The ground-station API listens on `http://localhost:8000`. Telemetry is
stored in a SQLite database in the `data/` directory on the host.

You can inspect the latest telemetry via:

```bash
curl http://localhost:8000/telemetry/latest
```

or open the interactive API docs at:

- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)

## 5. QEMU / Embedded Linux Integration

In this repository the satellite node runs as a normal Docker container
based on a Python image. For more realism in an embedded context, the
`satellite-node` component can also be deployed as part of an ARM Linux
root filesystem and executed under QEMU (e.g. `qemu-system-arm`).

The file `satellite-node/qemu-run-notes.md` sketches a possible setup for:

- building a minimal ARM rootfs (BusyBox, Python, sat_agentd.py)
- booting it with QEMU
- exposing network connectivity so that the virtual satellite can reach the
  ground-station container

This allows you to demonstrate familiarity with QEMU-based embedded Linux
testing without requiring complex tooling in this prototype.

## 6. How This Relates to the Job Profile

This project is designed to illustrate:

- **Erfahrungen im Bereich der Satellitentechnik**  
  through the modelling of orbits, contact windows and a satellite
  ground-segment architecture.

- **Erfahrungen im Bereich der Informationssicherheit**  
  through HMAC-protected telemetry / commands, basic replay protection,
  separation of roles and a dedicated security monitoring component.

The repository can be referenced in applications to roles that involve
satellite-based Early Warning systems, secure communications,
Informationssicherheit and IT-Architektur in a defence context.
