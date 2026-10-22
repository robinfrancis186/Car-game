#include "CoastalHUD.h"
#include "CoastalCarPawn.h"
#include "CoastalRaceDirector.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"
void ACoastalHUD::Label(const FString& T,float X,float Y,float S,const FLinearColor& C){DrawText(T,C,X,Y,GEngine->GetSmallFont(),S,false);}
FString ACoastalHUD::TimeLabel(float S)const{return FString::Printf(TEXT("%02d:%05.2f"),int(S/60),FMath::Fmod(S,60.f));}
void ACoastalHUD::DrawHUD(){
 Super::DrawHUD();if(!Canvas)return;
 ACoastalCarPawn* Car=Cast<ACoastalCarPawn>(GetOwningPawn());if(!Car)return;
 const float W=Canvas->ClipX,H=Canvas->ClipY,S=FMath::Max(.6f,H/1080.f);
 const FLinearColor Ink(.015f,.04f,.055f,.82f),White(.94f,.96f,.94f,1),Mint(.26f,.93f,.74f,1),Muted(.63f,.75f,.76f,1);
 DrawRect(Ink,30*S,30*S,460*S,132*S);DrawRect(Mint,30*S,30*S,4*S,132*S);
 Label(TEXT("M A L A B A R"),52*S,43*S,2.1f*S,White);
 Label(TEXT("KAPPIL COAST  /  KERALA"),52*S,88*S,1.05f*S,Mint);
 ACoastalRaceDirector* R=Car->Race;
 if(R){
  Label(TimeLabel(R->RaceTime),52*S,117*S,1.5f*S,White);
  Label(FString::Printf(TEXT("GATE  %02d / %02d"),FMath::Min(R->NextCheckpoint,R->Checkpoints.Num()-1),R->Checkpoints.Num()-1),270*S,121*S,S,Muted);
  DrawRect(FLinearColor(.1,.2,.22,.7),30*S,170*S,460*S,4*S);DrawRect(Mint,30*S,170*S,460*S*R->Progress(),4*S);
  if(R->BestTime>0)Label(TEXT("BEST  ")+TimeLabel(R->BestTime),36*S,185*S,S,Muted);
  if(R->Countdown>0){DrawRect(Ink,W*.5-100*S,H*.42-60*S,200*S,130*S);Label(FString::FromInt(FMath::CeilToInt(R->Countdown)),W*.5-22*S,H*.42-44*S,5*S,Mint);}
  if(R->Finished){DrawRect(Ink,W*.5-300*S,H*.42-100*S,600*S,220*S);Label(TEXT("COAST COMPLETE"),W*.5-205*S,H*.42-75*S,2.7f*S,Mint);Label(TimeLabel(R->RaceTime),W*.5-120*S,H*.42-15*S,3*S,White);Label(TEXT("ENTER  /  RACE AGAIN"),W*.5-130*S,H*.42+65*S,1.2f*S,White);}
 }
 DrawRect(Ink,W-310*S,H-220*S,280*S,180*S);
 Label(FString::Printf(TEXT("%03d"),FMath::RoundToInt(Car->SpeedKph())),W-290*S,H-214*S,5*S,White);
 Label(TEXT("KM / H"),W-122*S,H-152*S,1.1f*S,Mint);
 Label(Car->IsFlying()?TEXT("AIRBORNE / ARCADE THRUST"):Car->FlightArmed()?TEXT("THRUST ARMED"):TEXT("ROAD MODE"),W-290*S,H-111*S,.95f*S,Muted);
 DrawRect(FLinearColor(.11,.22,.24,1),W-290*S,H-70*S,240*S,6*S);DrawRect(Mint,W-290*S,H-70*S,240*S*Car->Energy(),6*S);
 Label(TEXT("WASD DRIVE   SPACE BRAKE   SHIFT BOOST   F FLIGHT   Q/E LIFT"),36*S,H-74*S,.92f*S,White);
 Label(TEXT("C CAMERA   MOUSE ORBIT   WHEEL ZOOM   R RECOVER (+5s)   ENTER RESTART   ESC PAUSE"),36*S,H-47*S,.86f*S,Muted);
 Label(TEXT("Closed game course | Original fan-made 2017 concept-inspired car | Arcade flight, not production simulation"),36*S,H-24*S,.65f*S,Muted);
 if(UGameplayStatics::IsGamePaused(GetWorld())){DrawRect(Ink,W*.5-250*S,H*.5-65*S,500*S,130*S);Label(TEXT("PAUSED  /  ESC TO RESUME"),W*.5-220*S,H*.5-20*S,2*S,White);}
}
