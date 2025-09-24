import os
import msvcrt
from filesystem import filesystem, header
from filesystem import commands
from kd.KD_Recorder import capture_password_with_kd

def flush_stdin():
    """Clear leftover input so password keystrokes don't spill into CLI."""
    while msvcrt.kbhit():
        msvcrt.getch()

# ---------------- Constants ----------------
REAL_VOLUME_FSID = 0
DECOY_VOLUME_FSID = 1

# ---------------- Main ----------------
def main():
    try:
        if not filesystem.vault_exists():
            print("No vault found, creating new volumes...")
            real_pass = input("Enter password for REAL volume: ")
            decoy_pass = input("Enter password for DECOY volume: ")
            try:
                filesystem.create_new_volume(real_pass, REAL_VOLUME_FSID)
                filesystem.create_new_volume(decoy_pass, DECOY_VOLUME_FSID)

                # 👉 Create extra header pointing to decoy (slot 1),
                # encrypted with the real password, written at slot 2
                filesystem.create_header_pointing_to_slot(
                    target_slot=DECOY_VOLUME_FSID,  # points to decoy
                    new_password=real_pass,         # encrypt header with real password
                    write_slot=2                    # store it in slot 2
                )

                print("Both volumes created successfully.\n")
            except Exception as e:
                print("Failed to create volumes:", e)
                return

        # ---------------- Password Prompt ----------------
        while True:
            password, kd_result = capture_password_with_kd()
            print(f"[DEBUG] KD result = {kd_result}")
            mounted_idx = None
            flush_stdin()
            try:
                mounted_idx, fsid = filesystem.mount(password, kd_result)
            except Exception:
                pass

            if mounted_idx is not None:
                print(f"Volume {fsid} mounted successfully.\n")
                break
            else:
                print("Incorrect password, try again.\n")

        # ---------------- CLI Loop ----------------
        print("\n--- Python Filesystem CLI ---")
        print("Type 'quit' to exit.")
        while True:
            user_input = input(f"fs:/> ").strip()
            if user_input.lower() in ("quit", "exit"):
                print("Exiting...")
                break
            commands.handle_command(user_input)

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting...")

if __name__ == "__main__":
    main()
