# AirTrack 0.9.0 "Orville"

**"AirTrack wasn't born — it was airlifted out, kicking, screaming, and waving a pilot's license!"** 🐷💄🛫😂

---

## About AirTrack

AirTrack is a **locally installed**, **offline-first** aircraft tracking system built for aviation enthusiasts, plane spotters, and serious aircraft data managers.

It began over **two years ago** as a simple idea for a Pi-based field spotting setup, evolving through sleepless nights, heartbreaks, coding marathons, and countless real-world field tests.
Today, it has become a full database-driven, multi-system, resilient aircraft tracking suite.

This is **not** a cloud-based system.
**Your data stays with you.**
You are the Captain.

---

## Current Version

| Field | Info |
|:------|:-----|
| **Version** | 0.9.0 |
| **Codename** | Orville |
| **Release Date** | 19 May 2025 |
| **Codename Meaning** | Honoring **Orville Wright**, pilot of the first controlled powered flight at Kitty Hawk, North Carolina on **17 December 1903**. |

---

## Features

- ✈️ Manage Airlines and Aircraft Registrations
- 📸 Upload and Manage Aircraft Images
- 🛬 Full Flight History and Sightings Tracker
- 🖥️ Local Website Interface (Flask + MariaDB backend)
- 🐧 Supports Linux Desktop and Raspberry Pi OS
- 🚀 One-Click Installer (Dockerized install process)
- 🔒 100% Offline and Local Storage — no remote servers involved
- 📈 Future-ready reporting and bug tracking

---

## System Requirements

| Component | Requirement |
|:----------|:-------------|
| Operating System | Linux Desktop (Ubuntu/Pop!_OS/Debian) or Raspberry Pi OS |
| Docker | Installed (Installer will install if missing) |
| Docker Compose | Installed (Installer will install if missing) |
| RAM | 2GB minimum recommended |
| Storage | Stable SSD or SD Card (for Pi) |
| Browser | Modern browser (Chrome, Firefox, Edge, etc.) |

---

## Installation Instructions

1. Download and unzip the Installer Package.
2. Open a Terminal inside the unzipped folder.
3. Make the install script executable:
   ```
   chmod +x install_airtrack.sh
   ```
4. Run the installer:
   ```
   ./install_airtrack.sh
   ```
5. Follow the on-screen prompts:
   - Set your MySQL username and password (for internal use)
   - Wait while AirTrack installs automatically
6. After installation, open your web browser and visit:
   ```
   http://localhost:5000
   ```

You are now flying with AirTrack!

---

## Supported Systems

| System | Status |
|:-------|:-------|
| Linux Desktop (Ubuntu, Pop!_OS, Mint) | ✅ Supported |
| Raspberry Pi OS (64-bit) | ✅ Supported |
| Debian-based distros | ✅ Should work | If not, let us know |
| Windows and Mac (via Docker Desktop) | 🚧 Planned for future versions |

---

## Roadmap

- 📈 Expand reports and analytics for sightings and trends
- 🗺️ Offline mapping integration for spotting locations
- 🛫 Add field capture improvements
- 📦 Full Windows & Mac Docker Installers
- 🔄 Centralized optional registry update syncing
- 🐞 Integrated BugTracker system with secure user authentication
- 🎖️ Extended pilot-themed release system ("The Legends of Flight" series)

---

## AirTrack Release Codenames

Each AirTrack release is named after an aviation pioneer — honoring history.

| Version | Codename | Reason |
|:--------|:---------|:-------|
| 0.9.0 | Orville | Honoring Orville Wright, pilot of the first powered flight (1903) |

Future versions will follow in historical order, honoring both Australian and international aviation legends.

---

## AirTrack Development History

AirTrack started life in **late 2022** as a field spotting experiment using a Raspberry Pi setup.
It evolved through **2023** into a Pi-based detection system capturing aircraft registration numbers.

By **early 2024**, the idea expanded into building a complete database-backed, user-friendly aircraft tracking system for personal use — culminating today with the release of **AirTrack 0.9.0 "Orville"**.

AirTrack has been a journey of:

- Late nights
- Fieldwork adventures
- Data disasters (and recoveries)
- Database rebuilds
- Countless cups of coffee
- Relentless passion for aviation

---

## License

- AirTrack is **Proprietary Software**.
- Redistribution or resale is not permitted without express permission.
- Your local data belongs entirely to you — we do not collect or access it.

---

## Acknowledgments

- ✈️ **Captain Trevor** — Founder, Visionary, Architect of AirTrack
- 🛬 Bob (Sir Robert of AirTrack) — Project co-pilot, always ready to assist and share a laugh
- ✈️ **Samowal** — The man without whose expertise this never would have been started and to whom I owe a debt of gratitude
- 🐷 Miss Piggy — Spiritual mascot of AirTrack Solutions 😂
- 🛩️ Every plane spotter who dreams big and looks up at the skies

---

# Final Boarding Call

> "**AirTrack wasn't born — it was airlifted out, kicking, screaming, and waving a pilot's license!**" 🐷💄🛫😂

Welcome aboard, Pilot.
Clear skies and tailwinds.
🛫🛬🛫

## Author

Developed by
Samowal - Devvista - http://devvista.org (original php version)
&
Trevor - AirTrack Solutions - http://airtracksolutions.com (current python version)
