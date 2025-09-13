#!/usr/bin/env bash
set -euo pipefail

# Config (hardcoded key path)
AGE_PRIV_KEY="${HOME}/.ssh/age.txt"

# Dependencies
REQUIRED_CMDS=(age age-keygen zip unzip zipinfo file)

# Variables
TEMP_FILES=()

usage() {
  cat <<EOF
Usage:
  $0 e <path>     Encrypt file or folder at <path>.
  $0 d [path]     Decrypt a .age file. If omitted, decrypt all *.age in cwd.

Encrypt (e):
  - File   -> wraps file into a zip (to preserve original filename), outputs <same-base>.age
  - Folder -> zips (excluding .DS_Store), outputs <folder-name>.age

Decrypt (d):
  - If plaintext is a zip:
      * Single-file zip -> extracts the file into the parent directory (restores original filename/ext).
      * Folder zip      -> extracts into a folder named after the .age base.
  - Otherwise, writes plaintext to the .age base file.
EOF
}

die() {
    echo "Error: $*" >&2
    exit 1
}

# Add a file to a list to be cleaned up on script exit
add_temp_file() {
  TEMP_FILES+=("$1")
}

# Clean up all temporary files
cleanup() {
  if [[ ${#TEMP_FILES[@]} -gt 0 ]]; then
    echo "Cleaning up temporary files..." >&2
    rm -f "${TEMP_FILES[@]}"
  fi
}

# Resolve absolute paths (macOS-safe, no GNU flags)
abspath() {
  local p="$1"
  case "$p" in
    "~" | "~/"* ) p="${p/#\~/$HOME}";;
  esac
  if [[ "$p" != /* ]]; then
    p="$PWD/$p"
  fi
  local dir base
  dir="$(dirname "$p")"
  base="$(basename "$p")"
  ( cd "$dir" >/dev/null 2>&1 && printf '%s/%s\n' "$(pwd)" "$base" )
}

encrypt_file() {
  local path="$1"
  local dir="$(dirname "$path")"
  local base="$(basename "$path")"
  local filename_no_ext="${base%.*}"
  local out="${dir}/${filename_no_ext}.age"
  local tmpzip="$(mktemp -t "${filename_no_ext}.XXXXXX").zip"

  echo "Zipping file to preserve name/extension ..."
  (
    cd "$dir"
    # Zip the single file by basename (no DS_Store concern here)
    zip -qX "$tmpzip" "$base"
  )

  echo "Encrypting file archive:"
  echo "  src zip: $tmpzip"
  echo "  out     : $out"
  age -r "$RECIPIENT" -o "$out" "$tmpzip"
  add_temp_file "$tmpzip"
}

encrypt_folder() {
  local path="$1"
  local dir="$(dirname "$path")"
  local base="$(basename "$path")"
  local folder_name="$base"

  tmpzip="$(mktemp -t "${folder_name}.XXXXXX").zip"
  echo "Zipping folder contents (excluding .DS_Store) ..."
  (
      cd "$dir/$folder_name"
      # zip the contents of the folder (.), preserving structure but NOT including the top-level folder
      # -r recursive, -q quiet, -X omit extra attrs; exclude .DS_Store anywhere and __MACOSX just in case
      zip -rqX "$tmpzip" . -x "*/.DS_Store" ".DS_Store" "__MACOSX/*"
  )
  out="${dir}/${folder_name}.age"
  echo "Encrypting folder archive:"
  echo "  src zip: $tmpzip"
  echo "  out     : $out"
  age -r "$RECIPIENT" -o "$out" "$tmpzip"
  add_temp_file "$tmpzip"
}

decrypt() {
  local in="$1"
  [[ -f "$in" ]] || die "Not a file: $in"
  [[ "$in" == *.age ]] || die "Input must end with .age: $in"

  local abs="$(abspath "$in")"
  local dir="$(dirname "$abs")"
  local base="$(basename "$abs" .age)"
  local tmp="$(mktemp -t "${base}.XXXXXX")"

  echo "Decrypting:"
  echo "  in : $abs"
  age -d -i "$AGE_PRIV_KEY" -o "$tmp" "$abs"

  # Check mime type to see if it is a zip
  local mt
  mt="$(file -b --mime-type "$tmp" || true)"

  if [[ "$mt" == "application/zip" ]]; then
    # Distinguish single-file zip vs folder zip
    local single
    if single="$(zip_is_single_file "$tmp")"; then
      # Single file -> extract directly into parent directory, preserve original name/ext
      echo "Single-file archive detected; extracting file into parent directory."
      (
        cd "$dir"
        unzip -qo "$tmp" "$single"
      )
      add_temp_file "$tmp"
    else
      # Folder archive -> extract into folder named after .age base
      local outdir="${dir}/${base}"
      mkdir -p "$outdir"
      echo "Folder archive detected; extracting to:"
      echo "  out dir: $outdir"
      unzip -q "$tmp" -d "$outdir"
      add_temp_file "$tmp"
    fi
  else
    # Plain file -> write to <base> (legacy case; not used when we zipped inputs)
    local outfile="${dir}/${base}"
    echo "Plain file detected; writing to:"
    echo "  out: $outfile"
    mv -f "$tmp" "$outfile"
  fi
}

# Set a trap to clean up temporary files on script exit.
trap cleanup EXIT

# Check deps
for cmd in "${REQUIRED_CMDS[@]}"; do
  command -v "$cmd" >/dev/null 2>&1 || die "Missing dependency: $cmd"
done

# Check key
[[ -f "$AGE_PRIV_KEY" ]] || die "Private key not found at: $AGE_PRIV_KEY"
RECIPIENT="$(age-keygen -y "$AGE_PRIV_KEY" 2>/dev/null || true)"
[[ -n "${RECIPIENT}" ]] || die "Could not derive recipient from private key at $AGE_PRIV_KEY"

# Helper: return 0 if zip contains exactly one file (not a dir), 1 otherwise
zip_is_single_file() {
  # prints the single filename on stdout if true
  local z="$1"
  # List entries one per line
  # Exclude directory entries (lines ending with /)
  # Count remaining lines
  local lines
  lines="$(zipinfo -1 "$z" | sed '/\/$/d')"
  if [[ -n "$lines" ]] && [[ $(printf "%s\n" "$lines" | wc -l | tr -d ' ') -eq 1 ]]; then
    printf "%s" "$lines"
    return 0
  fi
  return 1
}

op="${1:-}"
case "$op" in
  e)
    path="${2:-}"; [[ -n "$path" ]] || { usage; exit 1; }
    path="$(abspath "$path")"
    [[ -e "$path" ]] || die "Path not found: $path"

    dir="$(dirname "$path")"
    base="$(basename "$path")"

    if [[ -f "$path" ]]
    then
      encrypt_file "$path"
    elif [[ -d "$path" ]]
    then
      encrypt_folder "$path"
    else
      die "Unsupported path type (not file or directory): $path"
    fi
    ;;

  d)
    target="${2:-}"
    if [[ -z "$target" ]]; then
      shopt -s nullglob
      files=( *.age )
      shopt -u nullglob
      [[ ${#files[@]} -gt 0 ]] || die "No .age files in current directory."
      for f in "${files[@]}"; do
        decrypt "$f"
      done
    else
      [[ -d "$target" ]] && die "For decryption, provide a .age file (not a directory)."
      decrypt "$target"
    fi
    ;;

  ""|-h|--help|help)
    usage
    ;;

  *)
    usage; exit 1;;
esac
