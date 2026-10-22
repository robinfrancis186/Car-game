#pragma once
// Original deterministic arcade motion core. SI units; no Unreal dependency.
// This is deliberately NOT a simulation of any Tesla production vehicle.
#include <algorithm>
#include <cmath>
namespace Malabar {
constexpr double Pi = 3.14159265358979323846;
inline double Clamp(double v,double lo,double hi){ return std::max(lo,std::min(hi,v)); }
struct Input { double throttle=0, steer=0, lift=0; bool brake=false, boost=false, flight=false; };
struct State { double x=0,y=0,z=0.5,yaw=0,speed=0,vz=0,steer=0,energy=1,wheelAngle=0; bool airborne=false; };
struct Tuning {
 double acceleration=12.0, braking=23.0, reverseAcceleration=5.0;
 double maximumSpeed=72.0, boostedSpeed=90.0, reverseSpeed=10.0;
 double wheelbase=2.70, wheelRadius=0.36, clearance=0.50;
 double maxSteer=0.48, maxLateralAcceleration=14.0;
 double drag=0.0021, rollingResistance=0.24, maxAltitude=12.0;
};
inline void Step(State& s, const Input& raw, double dt, double ground, const Tuning& t=Tuning{}) {
 if (!std::isfinite(dt) || dt<=0) return;
 dt=std::min(dt,1.0/60.0); // caller fixed-substeps elapsed time
 const double throttle=Clamp(raw.throttle,-1,1), steer=Clamp(raw.steer,-1,1);
 bool thrust=raw.flight && s.energy>0.005;
 bool boost=raw.boost && s.energy>0.005 && throttle>0 && !raw.brake;
 s.energy=Clamp(s.energy+dt*((thrust?-0.14:0)+(boost?-0.20:0)+(!thrust&&!boost?0.08:0)),0,1);
 const double desiredSteer=steer*t.maxSteer/(1+std::abs(s.speed)*0.022);
 s.steer+=(desiredSteer-s.steer)*(1-std::exp(-10*dt));
 double accel=throttle*(throttle>=0?t.acceleration:t.reverseAcceleration)*(boost?1.55:1.0);
 // Reverse control brakes first, only then starts reversing.
 if(throttle<0 && s.speed>0.35) accel=-t.braking;
 if(throttle>0 && s.speed<-.35) accel=t.braking;
 if(raw.brake) accel=0;
 double resistance=t.drag*s.speed*std::abs(s.speed);
 double next=s.speed+(accel-resistance)*dt;
 double friction=(raw.brake?t.braking:t.rollingResistance)*dt;
 next=next>0?std::max(0.0,next-friction):std::min(0.0,next+friction);
 s.speed=Clamp(next,-t.reverseSpeed,boost?t.boostedSpeed:t.maximumSpeed);
 double yawRate=s.speed/std::max(.1,t.wheelbase)*std::tan(s.steer);
 double yawLimit=t.maxLateralAcceleration/std::max(3.0,std::abs(s.speed));
 yawRate=Clamp(yawRate,-yawLimit,yawLimit)*(s.airborne?0.48:1.0);
 s.yaw=std::remainder(s.yaw+yawRate*dt,2*Pi);
 s.x+=std::cos(s.yaw)*s.speed*dt; s.y+=std::sin(s.yaw)*s.speed*dt;
 const double floor=ground+t.clearance;
 if(thrust){
   const double targetVz=2.8+Clamp(raw.lift,-1,1)*5.2;
   s.vz+=(targetVz-s.vz)*(1-std::exp(-2.5*dt));
 }else s.vz-=9.81*dt;
 s.z+=s.vz*dt;
 if(s.z<floor){s.z=floor;s.vz=0;}
 if(s.z>floor+t.maxAltitude){s.z=floor+t.maxAltitude;s.vz=std::min(0.0,s.vz);}
 s.airborne=s.z>floor+0.08;
 s.wheelAngle=std::remainder(s.wheelAngle+s.speed*dt/t.wheelRadius,2*Pi);
}
inline bool SegmentHitsGate(double ax,double ay,double bx,double by,double gx,double gy,double radius){
 const double dx=bx-ax,dy=by-ay,den=dx*dx+dy*dy;
 const double f=den>1e-12?Clamp(((gx-ax)*dx+(gy-ay)*dy)/den,0,1):0;
 const double ex=ax+f*dx-gx,ey=ay+f*dy-gy;
 return ex*ex+ey*ey<=radius*radius;
}
}
