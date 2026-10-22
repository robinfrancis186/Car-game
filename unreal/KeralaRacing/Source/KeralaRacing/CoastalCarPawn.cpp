#include "CoastalCarPawn.h"
#include "CoastalRaceDirector.h"
#include "Camera/CameraComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InputComponent.h"
#include "Components/AudioComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

ACoastalCarPawn::ACoastalCarPawn(){
 PrimaryActorTick.bCanEverTick=true;
 Collision=CreateDefaultSubobject<UBoxComponent>(TEXT("ChassisCollision"));
 SetRootComponent(Collision); Collision->SetBoxExtent(FVector(205,87,44));
 Collision->SetCollisionProfileName(TEXT("Pawn"));
 Collision->SetSimulatePhysics(false); // fixed-step arcade controller, not Chaos simulation
 Body=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BlenderBody"));
 Body->SetupAttachment(Collision);Body->SetRelativeLocation(FVector(0,0,-50));Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 WheelCenters={FVector(135,-92.4,36.8),FVector(135,92.4,36.8),FVector(-135,-92.4,36.8),FVector(-135,92.4,36.8)};
 const TCHAR* Names[]={TEXT("Wheel_FL"),TEXT("Wheel_FR"),TEXT("Wheel_RL"),TEXT("Wheel_RR")};
 for(int32 i=0;i<4;++i){
  USceneComponent* Pivot=CreateDefaultSubobject<USceneComponent>(*FString::Printf(TEXT("Steer_%d"),i));
  Pivot->SetupAttachment(Collision);Pivot->SetRelativeLocation(WheelCenters[i]-FVector(0,0,50));SteeringPivots.Add(Pivot);
  UStaticMeshComponent* Wheel=CreateDefaultSubobject<UStaticMeshComponent>(Names[i]);Wheel->SetupAttachment(Pivot);Wheel->SetCollisionEnabled(ECollisionEnabled::NoCollision);Wheels.Add(Wheel);
 }
 CameraBoom=CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));CameraBoom->SetupAttachment(Collision);
 CameraBoom->TargetArmLength=600;CameraBoom->SetRelativeLocation(FVector(0,0,80));CameraBoom->SetRelativeRotation(FRotator(-12,0,0));CameraBoom->bEnableCameraLag=true;CameraBoom->CameraLagSpeed=7;CameraBoom->CameraLagMaxDistance=180;CameraBoom->bDoCollisionTest=true;
 Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));Camera->SetupAttachment(CameraBoom,USpringArmComponent::SocketName);Camera->FieldOfView=76;
 Motor=CreateDefaultSubobject<UAudioComponent>(TEXT("ElectricMotor"));Motor->SetupAttachment(Collision);Motor->bAutoActivate=false;
}
void ACoastalCarPawn::BeginPlay(){
 Super::BeginPlay();
 if(UStaticMesh* M=LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Vehicles/CarBody.CarBody")))Body->SetStaticMesh(M);
 const TCHAR* Paths[]={TEXT("/Game/Vehicles/Wheel_FL.Wheel_FL"),TEXT("/Game/Vehicles/Wheel_FR.Wheel_FR"),TEXT("/Game/Vehicles/Wheel_RL.Wheel_RL"),TEXT("/Game/Vehicles/Wheel_RR.Wheel_RR")};
 for(int32 i=0;i<4;++i){if(UStaticMesh* M=LoadObject<UStaticMesh>(nullptr,Paths[i]))Wheels[i]->SetStaticMesh(M);if(WheelCenters.IsValidIndex(i))SteeringPivots[i]->SetRelativeLocation(WheelCenters[i]-FVector(0,0,50));}
 for(TActorIterator<ACoastalRaceDirector> It(GetWorld());It;++It){Race=*It;break;}
 if(USoundBase* S=LoadObject<USoundBase>(nullptr,TEXT("/Game/Audio/EV_Loop.EV_Loop"))){Motor->SetSound(S);Motor->SetVolumeMultiplier(.16f);Motor->Play();}
 const FVector P=GetActorLocation();Motion.x=P.X/100;Motion.y=P.Y/100;Motion.z=P.Z/100;Motion.yaw=FMath::DegreesToRadians(GetActorRotation().Yaw);
 if(APlayerController* PC=Cast<APlayerController>(GetController())){PC->SetInputMode(FInputModeGameOnly());PC->bShowMouseCursor=false;}
}
void ACoastalCarPawn::Tick(float Dt){
 Super::Tick(Dt);
 if(!FMath::IsFinite(Dt))return;
 Accumulator+=FMath::Min(Dt,.1f);
 constexpr double Fixed=1.0/120.0;
 while(Accumulator>=Fixed){
  Malabar::Input I=Controls;
  if(Race&&!Race->CanDrive()){I=Malabar::Input{};I.brake=true;}
  FHitResult Ground;FCollisionQueryParams Params(SCENE_QUERY_STAT(CarGround),false,this);
  const FVector Pos=GetActorLocation();
  const bool Found=GetWorld()->LineTraceSingleByChannel(Ground,Pos,Pos-FVector(0,0,5000),ECC_Visibility,Params);
  const double Floor=Found?Ground.ImpactPoint.Z/100.0:-30.0;
  Malabar::Step(Motion,I,Fixed,Floor);
  FHitResult Hit;
  SetActorLocationAndRotation(FVector(Motion.x*100,Motion.y*100,Motion.z*100),FRotator(0,FMath::RadiansToDegrees(Motion.yaw),0),true,&Hit,ETeleportType::None);
  if(Hit.bBlockingHit){
   const FVector Actual=GetActorLocation();Motion.x=Actual.X/100;Motion.y=Actual.Y/100;Motion.z=Actual.Z/100;
   if(FMath::Abs(Hit.ImpactNormal.Z)<.6f)Motion.speed*=.12;else if(Motion.vz<0)Motion.vz=0;
  }
  if(Motion.energy<=.005)Controls.flight=false;
  Accumulator-=Fixed;
 }
 for(int32 i=0;i<4;++i){
  SteeringPivots[i]->SetRelativeRotation(FRotator(0,i<2?FMath::RadiansToDegrees(Motion.steer):0,0));
  Wheels[i]->SetRelativeRotation(FRotator(-FMath::RadiansToDegrees(Motion.wheelAngle),0,0));
 }
 const float Roll=FMath::Clamp(static_cast<float>(-Motion.steer*Motion.speed*.12),-3.f,3.f);
 Body->SetRelativeRotation(FRotator(Motion.airborne?-3.f:0.f,0,Roll));
 Motor->SetPitchMultiplier(.5f+static_cast<float>(FMath::Abs(Motion.speed)/30));
 Motor->SetVolumeMultiplier(.08f+FMath::Abs(Controls.throttle)*.18f);
 UpdateCamera(Dt);
 if(GetActorLocation().Z<-1500)ResetCar();
}
void ACoastalCarPawn::SetupPlayerInputComponent(UInputComponent* In){
 Super::SetupPlayerInputComponent(In);
 In->BindAxis("Throttle",this,&ACoastalCarPawn::Throttle);In->BindAxis("Steer",this,&ACoastalCarPawn::Steer);In->BindAxis("Lift",this,&ACoastalCarPawn::Lift);
 In->BindAxis("LookYaw",this,&ACoastalCarPawn::LookYaw);In->BindAxis("LookPitch",this,&ACoastalCarPawn::LookPitch);In->BindAxis("Zoom",this,&ACoastalCarPawn::Zoom);
 In->BindAction("Brake",IE_Pressed,this,&ACoastalCarPawn::BrakeOn);In->BindAction("Brake",IE_Released,this,&ACoastalCarPawn::BrakeOff);
 In->BindAction("Boost",IE_Pressed,this,&ACoastalCarPawn::BoostOn);In->BindAction("Boost",IE_Released,this,&ACoastalCarPawn::BoostOff);
 In->BindAction("Flight",IE_Pressed,this,&ACoastalCarPawn::ToggleFlight);In->BindAction("Camera",IE_Pressed,this,&ACoastalCarPawn::CycleCamera);
 In->BindAction("Reset",IE_Pressed,this,&ACoastalCarPawn::ResetCar);In->BindAction("Restart",IE_Pressed,this,&ACoastalCarPawn::RestartRace);
 In->BindAction("Pause",IE_Pressed,this,&ACoastalCarPawn::TogglePause).bExecuteWhenPaused=true;
}
void ACoastalCarPawn::Throttle(float V){Controls.throttle=FMath::Clamp(V,-1.f,1.f);}void ACoastalCarPawn::Steer(float V){Controls.steer=FMath::Clamp(V,-1.f,1.f);}void ACoastalCarPawn::Lift(float V){Controls.lift=FMath::Clamp(V,-1.f,1.f);}
void ACoastalCarPawn::LookYaw(float V){OrbitYaw=FMath::Clamp(OrbitYaw+V*1.5f,-150.f,150.f);}void ACoastalCarPawn::LookPitch(float V){OrbitPitch=FMath::Clamp(OrbitPitch+V,-55.f,15.f);}void ACoastalCarPawn::Zoom(float V){ZoomDistance=FMath::Clamp(ZoomDistance-V*60,300.f,1200.f);}
void ACoastalCarPawn::BrakeOn(){Controls.brake=true;}void ACoastalCarPawn::BrakeOff(){Controls.brake=false;}void ACoastalCarPawn::BoostOn(){Controls.boost=true;}void ACoastalCarPawn::BoostOff(){Controls.boost=false;}
void ACoastalCarPawn::ToggleFlight(){Controls.flight=!Controls.flight;}void ACoastalCarPawn::CycleCamera(){CameraMode=(CameraMode+1)%3;ResetCameraLag=true;OrbitYaw=0;OrbitPitch=-12;}
void ACoastalCarPawn::ResetCar(){if(Race)Race->ResetCar(this,true);else TeleportToCourse(FVector(0,0,70),0);}
void ACoastalCarPawn::RestartRace(){if(Race)Race->Restart(this);}
void ACoastalCarPawn::TogglePause(){if(APlayerController* PC=Cast<APlayerController>(GetController()))PC->SetPause(!UGameplayStatics::IsGamePaused(GetWorld()));}
void ACoastalCarPawn::TeleportToCourse(const FVector& P,float Yaw){
 Motion=Malabar::State{};Motion.x=P.X/100;Motion.y=P.Y/100;Motion.z=P.Z/100;Motion.yaw=FMath::DegreesToRadians(Yaw);Controls.flight=false;Accumulator=0;ResetCameraLag=true;
 SetActorLocationAndRotation(P,FRotator(0,Yaw,0),false,nullptr,ETeleportType::TeleportPhysics);
}
void ACoastalCarPawn::UpdateCamera(float Dt){
 CameraBoom->bEnableCameraLag=(CameraMode==0&&!ResetCameraLag);
 ResetCameraLag=false;
 const float SpeedFov=FMath::Clamp(static_cast<float>(SpeedKph()/30),0.f,10.f);
 Camera->SetFieldOfView(FMath::FInterpTo(Camera->FieldOfView,76+SpeedFov,Dt,3));
 if(CameraMode==1){CameraBoom->TargetArmLength=0;CameraBoom->SetRelativeLocation(FVector(90,0,55));CameraBoom->SetRelativeRotation(FRotator(0,OrbitYaw*.3,0));}
 else if(CameraMode==2){CameraBoom->TargetArmLength=0;CameraBoom->SetRelativeLocation(FVector(-12,37,63));CameraBoom->SetRelativeRotation(FRotator(0,OrbitYaw*.4,0));}
 else{CameraBoom->TargetArmLength=ZoomDistance;CameraBoom->SetRelativeLocation(FVector(0,0,80));CameraBoom->SetRelativeRotation(FRotator(OrbitPitch,OrbitYaw,0));}
}
