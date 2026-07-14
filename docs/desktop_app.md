# Native desktop operator application

The recommended operator surface is the local Tkinter application. It reuses the same collectors,
ranking, approval stores, card renderer, PDD client, and synchronization log as the API without
starting a web server.

Start on Windows by double-clicking `启动桌面运营台.cmd`, or run:

```powershell
$env:PYTHONPATH="src"
python -m product_reco_bot.desktop.app
```

Installed editable projects also expose:

```powershell
reco-desktop
```

The web management API remains available for debugging and integration compatibility but is not
required by the desktop application.
