package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"file_system/filesystem"

	"golang.org/x/term"
)

func main() {
	for {
		// Case 1: Vault does not exist → create new
		if !filesystem.VaultExists() {
			fmt.Println("No vault found, type password to create new vault.")

			fmt.Print("Enter password: ")
			pwBytes, err := term.ReadPassword(int(os.Stdin.Fd()))
			fmt.Println()
			if err != nil {
				fmt.Println("Error reading password:", err)
				continue
			}
			password := string(pwBytes)

			if err := filesystem.CreateNewVolume(password); err != nil {
				fmt.Println("Failed to create vault:", err)
				continue
			}
			fmt.Println("Vault created successfully.")
			fmt.Println("")
			break
		}

		// Case 2: Vault exists → ask for password & try to mount
		fmt.Print("Enter password: ")
		pwBytes, err := term.ReadPassword(int(os.Stdin.Fd()))
		fmt.Println()
		if err != nil {
			fmt.Println("Error reading password:", err)
			continue
		}
		password := string(pwBytes)

		if err := filesystem.Mount(password); err != nil {
			fmt.Println("Incorrect password, try again.")
			continue
		}
		fmt.Println("Vault mounted successfully.")
		break
	}

	// Start FS CLI
	fmt.Println("--- Go Filesystem CLI ---")
	fmt.Println("Type 'quit' to exit.")

	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Printf("fs:%s> ", filesystem.GetCurrentPath())
		input, err := reader.ReadString('\n')
		if err != nil {
			fmt.Println("Error reading input:", err)
			continue
		}

		input = strings.TrimSpace(input)
		if input == "" {
			continue
		}
		if input == "quit" || input == "exit" {
			fmt.Println("Exiting...")
			break
		}

		handleCommand(input)
	}
}

func handleCommand(input string) {
	args := strings.Fields(input)
	if len(args) == 0 {
		return
	}

	cmd := args[0]
	params := args[1:]

	switch cmd {
	case "ls":
		filesystem.ListDir()
	case "tree":
		filesystem.PrintTree()
	case "cd":
		if len(params) != 1 {
			fmt.Println("Usage: cd <directory>")
		} else {
			filesystem.ChangeDir(params[0])
		}
	case "mkdir":
		if len(params) != 1 {
			fmt.Println("Usage: mkdir <directory>")
		} else {
			filesystem.MakeDir(params[0])
		}
	case "rmdir":
		if len(params) != 1 {
			fmt.Println("Usage: rmdir <directory>")
		} else {
			filesystem.RemoveDir(params[0])
		}
	case "create":
		if len(params) != 1 {
			fmt.Println("Usage: create <file>")
		} else {
			filesystem.CreateFile(params[0])
		}
	case "write":
		if len(params) < 2 {
			fmt.Println("Usage: write <file> <content>")
		} else {
			name := params[0]
			data := strings.Join(params[1:], " ")
			filesystem.WriteFile(name, data)
		}
	case "append":
		if len(params) < 2 {
			fmt.Println("Usage: append <file> <content>")
		} else {
			name := params[0]
			data := strings.Join(params[1:], " ")
			filesystem.AppendFile(name, data)
		}
	case "read":
		if len(params) != 1 {
			fmt.Println("Usage: read <file>")
		} else {
			filesystem.ReadFile(params[0])
		}
	case "rm":
		if len(params) != 1 {
			fmt.Println("Usage: rm <file>")
		} else {
			filesystem.RemoveFile(params[0])
		}
	default:
		fmt.Println("Unknown command:", cmd)
	}
}
