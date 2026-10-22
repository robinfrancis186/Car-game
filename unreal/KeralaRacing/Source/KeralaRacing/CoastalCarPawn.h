#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "DriveModel.h"
#include "CoastalCarPawn.generated.h"
class UBoxComponent; class UStaticMeshComponent; class USpringArmComponent; class UCameraComponent; class UAudioComponent; class ACoastalRaceDirector;
UCLASS()
class KERALARACING_API ACoastalCarPawn : public APawn {
 GENERATED_BODY()
public:
 ACoastalCarPawn();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) UBoxComponent* Collision;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) UStaticMeshComponent* Body;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) TArray<USceneComponent*> SteeringPivots;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) TArray<UStaticMeshComponent*> Wheels;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) USpringArmComponent* CameraBoom;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) UCameraComponent* Camera;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) UAudioComponent* Motor;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Vehicle") TArray<FVector> WheelCenters;
 UPROPERTY(BlueprintReadOnly) ACoastalRaceDirector* Race=nullptr;
 double SpeedKph()const{return FMath::Abs(Motion.speed)*3.6;}
 double Energy()const{return Motion.energy;}
 bool IsFlying()const{return Motion.airborne;}
 bool FlightArmed()const{return Controls.flight;}
 int32 GetCameraMode()const{return CameraMode;}
 void TeleportToCourse(const FVector& Location,float YawDegrees);
private:
 Malabar::State Motion;
 Malabar::Input Controls;
 double Accumulator=0;
 float OrbitYaw=0,OrbitPitch=-12,ZoomDistance=600;
 int32 CameraMode=0;
 bool ResetCameraLag=true;
 void Throttle(float v);void Steer(float v);void Lift(float v);
 void LookYaw(float v);void LookPitch(float v);void Zoom(float v);
 void BrakeOn();void BrakeOff();void BoostOn();void BoostOff();
 void ToggleFlight();void CycleCamera();void ResetCar();void RestartRace();void TogglePause();
 void UpdateCamera(float dt);
};
