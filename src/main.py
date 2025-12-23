# I know this looks like alot of imports, and it is, but like idk, you can try to add the functions manually if you want to.

import typer
import platform
import os
from rich.console import Console
import tomllib
from urllib.request import urlretrieve
import zipfile
import shutil
import pynxm  # Nexus Mods API

app = typer.Typer()
console = Console()


with open("cuddle.toml", "rb") as f:
    config = tomllib.load(f)

# LOGIC FOR EVERYTHING BASICALLY
operatingSystem = platform.system()
subnauticaPath = None
warnWineCFG = False
steam_warning = config["settings"]["steam_warning"]
bepinex_Address = "https://github.com/toebeann/BepInEx.Subnautica/releases/latest/download/Tobey.s.BepInEx.Pack.for.Subnautica.zip"


match operatingSystem:
    case "Linux":
        subnauticaPath = os.path.expanduser("~/.local/share/Steam/steamapps/common/Subnautica")
        warnWineCFG = True
    case "Windows":
        subnauticaPath = "None"
    case "Darwin":  # For some reason MacOS is called Darwin idk bro
        subnauticaPath = "None"
        warnWineCFG = True


@app.command()
def listdirectories():
    os.listdir()


@app.command()
def init():
    if warnWineCFG and steam_warning:
        console.print('''Remember to add    [bold]WINEDLLOVERRIDES="winhttp=n,b" %command%[/]    to your Steam launch settings
[bold]Tip: To not get this warning change steam_warning in cuddle.toml to false.[/]''')

    console.print("[blue]Installing BepInEx...[/]")
    urlretrieve(bepinex_Address, "BepInEx.zip")
    with zipfile.ZipFile("BepInEx.zip", 'r') as zip_ref:
        zip_ref.extractall(subnauticaPath)
    console.print("[green]Installed BepInEx...[/]")
    console.print("[red]Deleting BepInEx's installation file...[/]")
    os.remove("BepInEx.zip")


@app.command()
def uninstall():
    if not subnauticaPath:
        console.print("You either are using a weird ass OS or it's just not set, just add a PR to the github and add your operating system.")
        return

    for name in ["BepInEx", "changelog.txt", "doorstop_config.ini", "libdoorstop.dylib", "run_bepinex.sh", "winhttp.dll"]:
        file = os.path.join(subnauticaPath, name)
        if os.path.isfile(file):
            os.remove(file)
        elif os.path.isdir(file):
            shutil.rmtree(file)


if __name__ == "__main__":
    app()
