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
from rich.progress import Progress
import time
import threading
from rich.table import Table
import re
from rich.tree import Tree
import requests
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

app = typer.Typer()
console = Console()


with open("../cuddle.toml", "rb") as f:
    config = tomllib.load(f)

# LOGIC FOR EVERYTHING BASICALLY
load_dotenv(dotenv_path="../.env")
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


def ProgressBar(name: str, waited_time: int, protime: float, **mkwargs):
    with Progress(**mkwargs) as progress_bar:
        task = progress_bar.add_task(name, total=waited_time)
        while not progress_bar.finished:
            progress_bar.update(task, advance=1)
            time.sleep(protime)

        return progress_bar


def add_nodes(tree, children):
    for item in children:
        if item["type"] == "directory":
            branch = tree.add(f"[bold blue]{item['name']}[/]")
            add_nodes(branch, item.get("children", []))
        else:
            tree.add(f"[green]{item['name']}[/] ({item['size']})")


@app.command()
def init(path: bool = typer.Option(False, "-b", "--bin", help="Add cuddle to your /bin hehe"),
        force: bool = typer.Option(False, "-f", "--force", help="Force installation even if already installed.")):
    '''
    Install [blue]BepInEx[/] and add cuddle to [green]PATH[/].
    '''

    if not subnauticaPath:
        console.print("You either are using a weird ass OS or it's just not set, just add a PR to the github and add your operating system.")
        return

    bepinex_missing = not os.path.exists(os.path.join(subnauticaPath, "BepInEx"))
    if not bepinex_missing and not force and not path:
        console.print("BepInEx is already installed. Use --force if this is a mistake.")
        return

    if not path:

        if warnWineCFG and steam_warning:
            console.print(
                "Remember to add [bold]WINEDLLOVERRIDES='winhttp=n,b' %command%[/] "
                "to your Steam launch settings\n"
                "[bold]Tip: To not get this warning, change steam_warning in cuddle.toml to false.[/]"
            )

        process = threading.Thread(target=ProgressBar, kwargs={"name": "Downloading BepInEx", "waited_time": 100, "protime": 0.003}, daemon=True)
        process.start()
        urlretrieve(bepinex_Address, "BepInEx.zip",)

        with zipfile.ZipFile("BepInEx.zip", 'r') as zip_ref:
            zip_ref.extractall(subnauticaPath)
        console.print("\n[green]Installed BepInEx...[/]")
        console.print("[red]Deleting BepInEx's installation file...[/]")
        os.remove("BepInEx.zip")

    if path and os.geteuid() != 0:
        os.execvp(
            "sudo",
            ["sudo", sys.executable, os.path.realpath(__file__)] + sys.argv[1:]
        )

    else:
        with open("/bin/cuddle", "w") as file:
            file.write(f'exec python {os.path.abspath(__file__)} "$@"\n')
        os.chmod("/bin/cuddle", mode=509)  # This is just like alot of bitwise OR just hard coded in


@app.command()
def uninstall(force: bool = typer.Option(False, "--force", "-f", help="Force uninstall even if BepInEx is not detected.")):
    '''
    Uninstall [blue]BepInEx[/] and all of the [b]related files[/].
    '''

    if not subnauticaPath:
        console.print("You either are using a weird ass OS or it's just not set, just add a PR to the github and add your operating system.")
        return
    bepinex_missing = not os.path.exists(os.path.join(subnauticaPath, "BepInEx"))
    if bepinex_missing and not force:
        console.print("BepInEx is not installed. Use --force if this is a mistake.")
        return

    for name in ["BepInEx", "changelog.txt", "doorstop_config.ini", "libdoorstop.dylib", "run_bepinex.sh", "winhttp.dll"]:
        file = os.path.join(subnauticaPath, name)

        if os.path.isfile(file):
            os.remove(file)
            ProgressBar(name=f"Uninstalling the file {file}", waited_time=100, protime=0.003)
        elif os.path.isdir(file):
            shutil.rmtree(file)
            ProgressBar(name=f"Uninstalling the folder {file}", waited_time=100, protime=0.003)


@app.command()
def info(mod_id, tree: bool = typer.Option(False, "--files", help="Display the contents of the mod in a tree because it looks cool")):
    '''
Gives [b]information[/] about mods' via the [i]ID[/], such as [b]version, filesize, filename,[/] and the [i]category[/] and the [b]structure[/] of the mod.
    '''

    mod_data = nxm.mod_file_list("subnautica", mod_id)
    files_list = mod_data.get("files", [])

    main_file = files_list[0]

    if not tree:
        # console.print(main_file["name"])
        console.print(main_file)

        ActualName = re.findall(r"[A-Z][a-z]*", main_file["name"])
        readable_name = " ".join(ActualName)

        # Create table for display
        table = Table(title=f"Info [b]{readable_name}[/]", show_lines=True)
        table.add_column("File Name", style="cyan", no_wrap=True)
        table.add_column("Version", style="magenta")
        table.add_column("Size (KB)", justify="right")
        table.add_column("Category", style="green")

        table.add_row(main_file["file_name"], main_file["version"], str(main_file["size_kb"]) + " KB", main_file["category_name"])

        console.print(table)

    else:
        response = requests.get(main_file["content_preview_link"])
        data = response.json()
        root_tree = Tree("[bold red]Mod Contents[/]")
        add_nodes(root_tree, data["children"])

        console.print(root_tree)


if __name__ == "__main__":
    app()
