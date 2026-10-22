#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CoastalRaceDirector.generated.h"
class ACoastalCarPawn;
UCLASS()
class KERALARACING_API ACoastalRaceDirector : public AActor {
 GENERATED_BODY()
public:
 ACoastalRaceDirector();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Course") TArray<FVector> Checkpoints;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Course") float GateRadius=750;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Course") FString CourseName=TEXT("KAPPIL COAST / 4.54 KM");
 UPROPERTY(BlueprintReadOnly) int32 NextCheckpoint=1;
 UPROPERTY(BlueprintReadOnly) float RaceTime=0;
 UPROPERTY(BlueprintReadOnly) float Countdown=3;
 UPROPERTY(BlueprintReadOnly) float BestTime=0;
 UPROPERTY(BlueprintReadOnly) float PenaltyTime=0;
 UPROPERTY(BlueprintReadOnly) bool Finished=false;
 bool CanDrive()const{return Countdown<=0&&!Finished&&Checkpoints.Num()>1;}
 void ResetCar(ACoastalCarPawn* Car,bool Penalize);
 void Restart(ACoastalCarPawn* Car);
 float Progress()const{return Checkpoints.Num()>1?float(NextCheckpoint-1)/(Checkpoints.Num()-1):0;}
private:
 FVector PreviousPosition=FVector::ZeroVector;
 bool HasPrevious=false;
};
