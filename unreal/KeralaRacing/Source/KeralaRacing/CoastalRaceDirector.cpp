#include "CoastalRaceDirector.h"
#include "CoastalCarPawn.h"
#include "DriveModel.h"
#include "Kismet/GameplayStatics.h"
#include "DrawDebugHelpers.h"
#include "Misc/ConfigCacheIni.h"
ACoastalRaceDirector::ACoastalRaceDirector(){PrimaryActorTick.bCanEverTick=true;}
void ACoastalRaceDirector::BeginPlay(){Super::BeginPlay();GConfig->GetFloat(TEXT("Malabar.Record"),TEXT("KappilBestSeconds"),BestTime,GGameUserSettingsIni);}
void ACoastalRaceDirector::Tick(float Dt){
 Super::Tick(Dt);
 ACoastalCarPawn* Car=Cast<ACoastalCarPawn>(UGameplayStatics::GetPlayerPawn(GetWorld(),0));if(!Car||Checkpoints.Num()<2)return;
 if(Countdown>0){Countdown=FMath::Max(0.f,Countdown-Dt);PreviousPosition=Car->GetActorLocation();HasPrevious=true;return;}
 if(Finished)return;
 RaceTime+=Dt;
 const FVector P=Car->GetActorLocation();if(!HasPrevious){PreviousPosition=P;HasPrevious=true;}
 if(Checkpoints.IsValidIndex(NextCheckpoint)){
  const FVector G=Checkpoints[NextCheckpoint];
  DrawDebugCircle(GetWorld(),G+FVector(0,0,25),GateRadius,48,FColor(72,232,194),false,0,0,5,FVector(1,0,0),FVector(0,1,0),false);
  DrawDebugLine(GetWorld(),G,G+FVector(0,0,1800),FColor(72,232,194),false,0,0,8);
  // Swept segment test prevents skipping a narrow checkpoint at high speed.
  if(FMath::Abs(P.Z-G.Z)<1600&&Malabar::SegmentHitsGate(PreviousPosition.X,PreviousPosition.Y,P.X,P.Y,G.X,G.Y,GateRadius)){
   ++NextCheckpoint;
   if(NextCheckpoint>=Checkpoints.Num()){
    Finished=true;
    if(BestTime<=0||RaceTime<BestTime){BestTime=RaceTime;GConfig->SetFloat(TEXT("Malabar.Record"),TEXT("KappilBestSeconds"),BestTime,GGameUserSettingsIni);GConfig->Flush(false,GGameUserSettingsIni);}
   }
  }
 }
 PreviousPosition=P;
}
void ACoastalRaceDirector::ResetCar(ACoastalCarPawn* Car,bool Penalize){
 if(!Car||Checkpoints.Num()<2)return;
 const int32 Index=FMath::Clamp(NextCheckpoint-1,0,Checkpoints.Num()-2);
 const FVector P=Checkpoints[Index]+FVector(0,0,70);
 const FVector Forward=Checkpoints[Index+1]-Checkpoints[Index];
 Car->TeleportToCourse(P,Forward.Rotation().Yaw);PreviousPosition=P;HasPrevious=true;
 if(Penalize&&!Finished&&Countdown<=0){RaceTime+=5;PenaltyTime+=5;}
}
void ACoastalRaceDirector::Restart(ACoastalCarPawn* Car){NextCheckpoint=1;RaceTime=0;PenaltyTime=0;Countdown=3;Finished=false;HasPrevious=false;ResetCar(Car,false);}
