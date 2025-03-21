### I got sick of dealing with the portableapps.com launcher, some things are just overly complicated for no real reason. 

### Wrote this quickly, has basic launcher features. WIP as I plan to add more, such as using symlinks instead of movie files/directories

# 🧰 Portable App Launcher

A flexible launcher for running portable Windows applications with custom configuration, registry virtualization, and cleanup logic.  
Designed for **isolating portable apps** while preserving user data between sessions.

---

## 📁 Directory Structure

```
PortableAppLauncher/
├── App/
│   ├── AppInfo/
│   │   └── Launcher/
│   │       ├── launcher.ini
│   │       └── splash.jpg (optional)
│   ├── DefaultData/          # Default files (copied on first run)
├── Data/
│   ├── Files/                # Persistent user data
│   ├── Reg/                  # Registry data (active session)
│   │   └── PreviousData/      # Registry data from previous session
├── launcher.exe              # Compiled launcher
```

---

## ⚙️ **launcher.ini Format**

### Required Fields

```ini
[Launch]
ProgramExecutable=App\MyApp\MyApp.exe
runasadmin=false
```

### Optional Sections

#### 🛠️ Debugging Mode

```ini
[Debug]
debug=1  # Enables verbose console + file logging
```

#### 📂 File Handling (`Data\Files`)

```ini
[DataFiles]
MyAppConfig=Data\Files\MyApp\Config.ini|%APPDATA%\MyApp\Config.ini
```

- On **launch**, copies `Data\Files\MyApp\Config.ini` → `%APPDATA%\MyApp\Config.ini`
- On **exit**, **saves changes** from `%APPDATA%\MyApp\Config.ini` back into `Data\Files\MyApp\Config.ini`

#### 🗑️ Registry Cleanup

```ini
[RegCleanup]
HKCU\Software\MyApp
HKLM\SOFTWARE\Example
```

- **Moves the previous registry session data** to `Data\Reg\PreviousData\`
- **Exports each key before deletion** into `Data\Reg\`
- **Deletes** the registry keys from the system

Example exported files:
```
Data\Reg\MyApp.reg
Data\Reg\Example.reg
```

> ⚠️ The **previous session’s** registry exports are stored in `Data\Reg\PreviousData\` before new exports happen.

#### 🧹 File Cleanup

```ini
[DataCleanup]
%APPDATA%\MyApp\Cache
```

- **Deletes** `Cache` folder from `%APPDATA%\MyApp` after the app exits.

---

## 🏗️ **How It Works**

### **🔽 On Launch**
1. **Loads `launcher.ini`**
2. **Moves previous registry exports** to `PreviousData/`
3. **Imports** all `.reg` files from `Data\Reg\`
4. **Copies files** as defined in `[DataFiles]`
5. **Runs `ProgramExecutable`**

### **🆗 While Running**
- Launcher **stays active** in the background.

### **🔼 On Exit**
1. **Exports & deletes** registry keys listed in `[RegCleanup]`
2. **Saves** modified files from `%APPDATA%` back into `Data\Files`
3. **Deletes** files listed in `[DataCleanup]`
4. **Moves previous `.reg` exports** into `Data\Reg\PreviousData\`

---

## 🚀 Features

- ✅ **Registry Import/Export** – Handles `.reg` files automatically.
- 🔐 **Admin Elevation** – Relaunches as admin if `runasadmin=true`.
- 🧹 **Registry & File Cleanup** – Removes leftover data after app exit.
- 🖼️ **Splash Screen Support** – Displays `splash.jpg` for 3 seconds if present.
- 🧾 **Debug Logging** – Stores logs when `[Debug] debug=1`.

---

## 📦 Future Improvements

- **Symlink Support** – Not yet implemented, but planned.
- **Auto-updater for portable apps**.
- **Profile-based configurations**.
- **GUI editor for `launcher.ini`**.

---

## 🧑‍💻 License

MIT License
