from . import filesystem, types

# ---------------- Directory & Navigation ----------------
def list_dir():
    if filesystem.current_dir is None:
        print("No current directory")
        return

    base = filesystem.get_current_path()
    for f in filesystem.file_entries:
        if getattr(f, "used", False) and f.path.startswith(base) and f.path != base:
            rel = f.path[len(base):].lstrip("/")
            if "/" not in rel:  # direct child only
                type_name = f.type.name if isinstance(f.type, types.FileType) else str(f.type)
                print(f"{f.name}\t({type_name})")


def print_tree():
    def _print_tree(base: str, level: int):
        prefix = "  " * level
        for f in filesystem.file_entries:
            if not getattr(f, "used", False) or not hasattr(f, "type"):
                continue
            if filesystem.parent_path(f.path) == base:
                name = f.name if f.name else "root"
                type_name = f.type.name if isinstance(f.type, types.FileType) else str(f.type)
                print(f"{prefix}{name}\t({type_name})")
                if f.type == types.FileType.DIRECTORY:
                    _print_tree(f.path, level + 1)

    _print_tree("", 0)


def change_dir(path: str):
    if path == "/":
        filesystem.current_dir = next((f for f in filesystem.file_entries if f.path == "/"), None)
        filesystem.current_path = [""]
        return

    full_path = filesystem.join_path(filesystem.get_current_path(), path)
    for f in filesystem.file_entries:
        if getattr(f, "used", False) and f.type == types.FileType.DIRECTORY and f.path == full_path:
            filesystem.current_dir = f
            filesystem.current_path = f.path.split("/")
            if filesystem.current_path[0] == "":
                filesystem.current_path = [""] + filesystem.current_path[1:]
            return
    print("Directory not found")


# ---------------- File Operations ----------------
def make_dir(name: str):
    new_path = filesystem.join_path(filesystem.get_current_path(), name)
    for f in filesystem.file_entries:
        if getattr(f, "used", False) and f.path == new_path:
            print("Directory already exists")
            return

    fe = filesystem.FileEntry(name=name, type=types.FileType.DIRECTORY, path=new_path, used=True)
    filesystem.file_entries.append(fe)
    print(f"Directory created: {name}")
    filesystem.save_filesystem()


def remove_dir(name: str):
    target = filesystem.join_path(filesystem.get_current_path(), name)
    for fe in filesystem.file_entries:
        if getattr(fe, "used", False) and fe.path == target:
            fe.used = False
            print(f"Directory removed: {name}")
            filesystem.save_filesystem()
            return
    print("Directory not found")


def create_file(name: str):
    new_path = filesystem.join_path(filesystem.get_current_path(), name)
    for f in filesystem.file_entries:
        if getattr(f, "used", False) and f.path == new_path:
            print("File exists")
            return

    fe = filesystem.FileEntry(name=name, type=types.FileType.FILE, path=new_path, used=True, content="")
    filesystem.file_entries.append(fe)
    print(f"File created: {name}")
    filesystem.save_filesystem()


def write_file(name: str, data: str):
    target = filesystem.join_path(filesystem.get_current_path(), name)
    for fe in filesystem.file_entries:
        if getattr(fe, "used", False) and fe.path == target:
            fe.content = data
            print(f"File written: {name}")
            filesystem.save_filesystem()
            return
    print("File not found")


def append_file(name: str, data: str):
    target = filesystem.join_path(filesystem.get_current_path(), name)
    for fe in filesystem.file_entries:
        if getattr(fe, "used", False) and fe.path == target:
            fe.content += data
            print(f"Data appended: {name}")
            filesystem.save_filesystem()
            return
    print("File not found")


def read_file(name: str):
    target = filesystem.join_path(filesystem.get_current_path(), name)
    for fe in filesystem.file_entries:
        if getattr(fe, "used", False) and fe.path == target:
            print(f"Contents of {name}:\n{fe.content}")
            return
    print("File not found")


def remove_file(name: str):
    target = filesystem.join_path(filesystem.get_current_path(), name)
    for fe in filesystem.file_entries:
        if getattr(fe, "used", False) and fe.path == target:
            fe.used = False
            print(f"File removed: {name}")
            filesystem.save_filesystem()
            return
    print("File not found")


# ---------------- Command Dispatcher ----------------
def handle_command(user_input: str):
    parts = user_input.strip().split()
    if not parts:
        return

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in ("ls", "dir"):
        list_dir()

    elif cmd == "tree":
        print_tree()

    elif cmd in ("cd", "chdir"):
        if not args:
            print("Usage: cd <directory>")
        else:
            change_dir(args[0])

    elif cmd == "mkdir":
        if not args:
            print("Usage: mkdir <name>")
        else:
            make_dir(args[0])

    elif cmd == "rmdir":
        if not args:
            print("Usage: rmdir <name>")
        else:
            remove_dir(args[0])

    elif cmd in ("touch", "create"):
        if not args:
            print("Usage: touch <filename>")
        else:
            create_file(args[0])

    elif cmd == "write":
        if len(args) < 2:
            print("Usage: write <filename> <data>")
        else:
            name, data = args[0], " ".join(args[1:])
            write_file(name, data)

    elif cmd == "append":
        if len(args) < 2:
            print("Usage: append <filename> <data>")
        else:
            name, data = args[0], " ".join(args[1:])
            append_file(name, data)

    elif cmd in ("cat", "read"):
        if not args:
            print("Usage: cat <filename>")
        else:
            read_file(args[0])

    elif cmd in ("rm", "del"):
        if not args:
            print("Usage: rm <filename>")
        else:
            remove_file(args[0])

    else:
        print(f"Unknown command: {cmd}")
