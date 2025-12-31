# I know this looks like alot of imports, and it is, but like idk, you can try to add the functions manually if you want to.

import typer
import platform
import os
from rich.console import Console
import tomllib
from urllib.request import urlretrieve
import zipfile
import shutil
from pynxm import Nexus  # Nexus Mods API
from dotenv import load_dotenv

app = typer.Typer()
console = Console()


with open("cuddle.toml", "rb") as f:
    config = tomllib.load(f)

# LOGIC FOR EVERYTHING BASICALLY
load_dotenv(dotenv_path=".env")
operatingSystem = platform.system()
subnauticaPath = None
warnWineCFG = False
steam_warning = config["settings"]["steam_warning"]
bepinex_Address = "https://github.com/toebeann/BepInEx.Subnautica/releases/latest/download/Tobey.s.BepInEx.Pack.for.Subnautica.zip"
api_key = os.getenv("API_KEY")
nxm = Nexus(api_key)


match operatingSystem:
    case "Linux":
        subnauticaPath = os.path.expanduser("~/.local/share/Steam/steamapps/common/Subnautica")
        warnWineCFG = True
    case "Windows":
        subnauticaPath = "None"
    case "Darwin":  # For some reason MacOS is called Darwin idk bro
        subnauticaPath = "None"
        warnWineCFG = True

if config["settings"]["subnautica_path"] != "":
    subnauticaPath = config["settings"]["subnauticaPath"]


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


@app.command()
def add(mod_id):
    mod_data = nxm.mod_file_list("subnautica", mod_id)
    files_list = mod_data.get("files", [])
    if not files_list:
        print(f"No downloadable files found for mod {mod_id}")
        return
    file_id = str(files_list[0]["file_id"])
    download_url = nxm.mod_file_download_link("subnautica", mod_id, file_id)
    print(f"Download URL: {download_url}")


if __name__ == "__main__":
    app()
