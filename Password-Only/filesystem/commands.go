package filesystem

import (
	"fmt"
	"strings"

	"file_system/types"
)

// ---------------- Directory & Navigation ----------------

func ListDir() {
	if currentDir == nil {
		fmt.Println("No current directory")
		return
	}

	base := GetCurrentPath()
	for _, f := range fileEntries {
		if f.Used && strings.HasPrefix(f.Path, base) && f.Path != base {
			rel := strings.TrimPrefix(f.Path, base)
			if strings.Count(rel, "/") == 1 {
				fmt.Printf("%s\t(%s)\n", f.Name, f.Type)
			}
		}
	}
}

func PrintTree() {
	base := ""
	printTreeRecursive(base, 0)
}

func printTreeRecursive(base string, level int) {
	prefix := strings.Repeat("  ", level)
	for _, f := range fileEntries {
		if f.Used && parentPath(f.Path) == base {
			fmt.Printf("%s%s\t(%s)\n", prefix, f.Name, f.Type)
			if f.Type == types.FileTypeDirectory {
				printTreeRecursive(f.Path, level+1)
			}
		}
	}
}

func ChangeDir(path string) {
	if path == "/" {
		currentDir = &fileEntries[0]
		currentPath = []string{""}
		return
	}

	fullPath := joinPath(GetCurrentPath(), path)
	for i, f := range fileEntries {
		if f.Used && f.Type == types.FileTypeDirectory && f.Path == fullPath {
			currentDir = &fileEntries[i]
			currentPath = strings.Split(f.Path, "/")
			if currentPath[0] == "" {
				currentPath = append([]string{""}, currentPath[1:]...)
			}
			return
		}
	}
	fmt.Println("Directory not found")
}

// ---------------- File Operations ----------------

func MakeDir(name string) {
	newPath := joinPath(GetCurrentPath(), name)
	for _, f := range fileEntries {
		if f.Used && f.Path == newPath {
			fmt.Println("Directory already exists")
			return
		}
	}
	for i := range fileEntries {
		if !fileEntries[i].Used {
			fileEntries[i] = types.FileEntry{
				Name: name, Type: types.FileTypeDirectory, Used: true, Path: newPath,
			}
			fmt.Println("Directory created:", name)
			SaveFilesystem()
			return
		}
	}
	fmt.Println("No free slots")
}

func RemoveDir(name string) {
	target := joinPath(GetCurrentPath(), name)
	for i := range fileEntries {
		if fileEntries[i].Used && fileEntries[i].Path == target {
			fileEntries[i].Used = false
			fmt.Println("Directory removed:", name)
			SaveFilesystem()
			return
		}
	}
	fmt.Println("Directory not found")
}

func CreateFile(name string) {
	newPath := joinPath(GetCurrentPath(), name)
	for _, f := range fileEntries {
		if f.Used && f.Path == newPath {
			fmt.Println("File exists")
			return
		}
	}
	for i := range fileEntries {
		if !fileEntries[i].Used {
			fileEntries[i] = types.FileEntry{Name: name, Type: types.FileTypeFile, Used: true, Path: newPath}
			fmt.Println("File created:", name)
			SaveFilesystem()
			return
		}
	}
	fmt.Println("No free slots")
}

func WriteFile(name, data string) {
	target := joinPath(GetCurrentPath(), name)
	for i := range fileEntries {
		if fileEntries[i].Used && fileEntries[i].Path == target {
			fileEntries[i].Content = data
			fmt.Println("File written:", name)
			SaveFilesystem()
			return
		}
	}
	fmt.Println("File not found")
}

func AppendFile(name, data string) {
	target := joinPath(GetCurrentPath(), name)
	for i := range fileEntries {
		if fileEntries[i].Used && fileEntries[i].Path == target {
			fileEntries[i].Content += data
			fmt.Println("Data appended:", name)
			SaveFilesystem()
			return
		}
	}
	fmt.Println("File not found")
}

func ReadFile(name string) {
	target := joinPath(GetCurrentPath(), name)
	for _, f := range fileEntries {
		if f.Used && f.Path == target {
			fmt.Println("Contents of", name, ":\n", f.Content)
			return
		}
	}
	fmt.Println("File not found")
}

func RemoveFile(name string) {
	target := joinPath(GetCurrentPath(), name)
	for i := range fileEntries {
		if fileEntries[i].Used && fileEntries[i].Path == target {
			fileEntries[i].Used = false
			fmt.Println("File removed:", name)
			SaveFilesystem()
			return
		}
	}
	fmt.Println("File not found")
}
