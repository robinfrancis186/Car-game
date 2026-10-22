#include "../unreal/KeralaRacing/Source/KeralaRacing/DriveModel.h"
#include <cassert>
#include <iostream>
#include <random>
using namespace Malabar;
void run(State& s,const Input& i,double seconds){for(int n=0;n<int(seconds*120);++n)Step(s,i,1.0/120.0,0);}
int main(){
 int tests=0;
 {State s;Input i;run(s,i,5);assert(s.speed==0&&std::abs(s.z-.5)<1e-9);++tests;}
 {State s;Input i;i.throttle=1;run(s,i,20);assert(s.speed>60&&s.speed<=72&&s.x>500);++tests;}
 {State s;Input i;i.throttle=1;run(s,i,5);i.throttle=0;i.brake=true;run(s,i,6);assert(std::abs(s.speed)<1e-9);++tests;}
 {State s;Input i;i.throttle=-1;run(s,i,10);assert(s.speed>=-10&&s.speed<0&&s.x<0);++tests;}
 {State s;Input i;i.throttle=1;i.steer=1;run(s,i,2);assert(s.y>0&&s.yaw>0);++tests;}
 {State s;Input i;i.flight=true;run(s,i,3);assert(s.z>.5&&s.z<=12.5&&s.airborne);i.flight=false;run(s,i,10);assert(s.z==.5&&!s.airborne);++tests;}
 {State s;Input i;i.flight=true;i.boost=true;i.throttle=1;run(s,i,60);assert(s.energy>=0&&s.energy<=1&&s.z<=12.5);++tests;}
 {State s;s.energy=.1;Input i;run(s,i,30);assert(s.energy==1);++tests;}
 {State s;Input i;i.throttle=100;i.steer=100;run(s,i,10);assert(s.speed<=72&&std::abs(s.steer)<=.48);++tests;}
 {assert(SegmentHitsGate(-10,0,10,0,0,0,1));assert(!SegmentHitsGate(-10,3,10,3,0,0,1));assert(SegmentHitsGate(0,0,0,0,0,0,1));++tests;}
 {State a,b;Input i;i.throttle=1;i.steer=.3;for(int j=0;j<600;++j)Step(a,i,1./60.,0);for(int j=0;j<1200;++j)Step(b,i,1./120.,0);assert(std::hypot(a.x-b.x,a.y-b.y)<1.5);++tests;}
 {State s;Input i;i.throttle=1;auto initial=s;Step(s,i,-1,0);Step(s,i,NAN,0);assert(s.x==initial.x);++tests;}
 {State s;std::mt19937 rng(33);std::uniform_real_distribution<double>u(-1,1);for(int k=0;k<100000;++k){Input i;i.throttle=u(rng);i.steer=u(rng);i.lift=u(rng);i.flight=u(rng)>.3;i.boost=u(rng)>.5;i.brake=u(rng)>.7;Step(s,i,1./120.,0);assert(std::isfinite(s.x)&&std::isfinite(s.y)&&std::isfinite(s.z)&&std::isfinite(s.speed));assert(s.energy>=0&&s.energy<=1&&s.z>=.5&&s.z<=12.5);}++tests;}
 std::cout<<"PASS "<<tests<<" standalone arcade motion tests; 100,000 randomized substeps. Unreal integration NOT tested.\n";
}
