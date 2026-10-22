#!/usr/bin/env bash
# Does not download or license Unreal; use an already approved official installation.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${UE_ROOT:?Set UE_ROOT to an installed, licensed official Unreal Engine 5.6+ directory}"
PROJECT="$ROOT/unreal/KeralaRacing/KeralaRacing.uproject"
case "${1:-editor}" in
 editor)
  "$UE_ROOT/Engine/Build/BatchFiles/Linux/Build.sh" KeralaRacingEditor Linux Development -Project="$PROJECT" -WaitMutex
  ;;
 bootstrap)
  "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" "$PROJECT" -ExecutePythonScript="$ROOT/unreal/KeralaRacing/Content/Python/bootstrap_project.py" -log
  ;;
 play)
  "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" "$PROJECT" /Game/Maps/KappilCoast -game -ResX=1920 -ResY=1080 -windowed -log
  ;;
 package)
  "$UE_ROOT/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun -project="$PROJECT" -noP4 -platform=Linux -clientconfig=Development -build -cook -map=/Game/Maps/KappilCoast -stage -pak -archive -archivedirectory="$ROOT/dist/Linux"
  ;;
 *) echo "Usage: UE_ROOT=/path/to/Unreal $0 {editor|bootstrap|play|package}" >&2;exit 2;;
esac
