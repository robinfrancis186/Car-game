#pragma once
#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "CoastalHUD.generated.h"
UCLASS()
class KERALARACING_API ACoastalHUD : public AHUD {
 GENERATED_BODY()
public: virtual void DrawHUD()override;
private:
 void Label(const FString& Text,float X,float Y,float Scale,const FLinearColor& Color);
 FString TimeLabel(float Seconds)const;
};
