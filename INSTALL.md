# AirTrack Lite Installation Guide

> ✨ Version 0.9.0 "Orville"

AirTrack Lite is a locally-installed, offline-first aircraft tracking system designed for aviation enthusiasts, spotters, and data managers.

This guide walks you through installing and running AirTrack Lite on Linux desktops, Raspberry Pi OS (64-bit), or Windows with Docker Desktop.

---

## 📅 Requirements

| Requirement     | Details                                                                                            |
| --------------- | -------------------------------------------------------------------------------------------------- |
| OS              | Ubuntu / Pop!\_OS / Debian / Raspberry Pi OS (64-bit), or Windows 10/11 with WSL2 & Docker Desktop |
| RAM             | 2 GB minimum recommended                                                                           |
| Disk Space      | 1 GB free (more if storing images)                                                                 |
| Tools Installed | None required in advance                                                                           |
| Internet        | Required only during installation                                                                  |

---

## 📦 Installation Steps (Linux / Raspberry Pi)

### 1. Download the Installer Package

Go to:

```
https://github.com/Subhuti/airtrack-lite/releases
```

You can also download it from:

```
http://airtracksolutions.com/downloads
```

Download the latest `.zip` archive:

```
AirTrack-Lite-0.9.0-Orville.zip
```

---

### 2. Extract the Archive

Open a terminal and extract it:

```bash
unzip AirTrack-Lite-0.9.0-Orville.zip -d AirTrack-Lite
cd AirTrack-Lite
```

---

### 3. Make the Installer Executable

```bash
chmod +x install_airtrack.sh
```

---

### 4. Run the Installer

```bash
./install_airtrack.sh
```

This script will:

* Install Docker & Docker Compose if not already present
* Decompress the compressed SQL database (`init.sql.gz`)
* Set up all containers and services
* Start the AirTrack Lite system

---

### 5. Open the Website

Once complete, open your browser and go to:

```
http://localhost:5000
```

Welcome to AirTrack Lite!

---

## 🪟 Installation Steps (Windows)

### 1. Install Prerequisites

* Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) and ensure WSL2 is enabled

### 2. Download & Extract

Download the `.zip` from either:

```
https://github.com/Subhuti/airtrack-lite/releases
```

or

```
http://airtracksolutions.com/downloads
```

Right-click and extract the contents to a new folder, e.g.:

```
C:\Users\YourName\AirTrack-Lite
```

### 3. Run the Installer (Lite Version)

Open **PowerShell** as Administrator, then:

```powershell
cd "C:\Users\YourName\AirTrack-Lite"
.\install_airtrack_windows.ps1
```

This Lite version script will:

* Check for Docker and pull required containers
* Decompress the `init.sql.gz` file
* Launch AirTrack Lite

### 4. Access the Site

Open your browser and visit:

```
http://localhost:5000
```

---

## ✅ Useful Commands

### To Start AirTrack Again Later:

Linux:

```bash
docker-compose up -d
```

Windows (PowerShell):

```powershell
docker-compose up -d
```

### To Stop AirTrack:

Linux:

```bash
docker-compose down
```

Windows (PowerShell):

```powershell
docker-compose down
```

---

## ⚡️ Troubleshooting

* Ensure you're running inside the extracted folder.
* Reboot if Docker isn't starting correctly.
* Still stuck? Visit:

```
http://airtracksolutions.com/help
```

---

AirTrack Lite © 2025 Trevor @ AirTrack Solutions. All rights reserved.
