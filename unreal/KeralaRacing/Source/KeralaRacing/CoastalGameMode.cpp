#include "CoastalGameMode.h"
#include "CoastalCarPawn.h"
#include "CoastalHUD.h"
ACoastalGameMode::ACoastalGameMode(){DefaultPawnClass=ACoastalCarPawn::StaticClass();HUDClass=ACoastalHUD::StaticClass();}
