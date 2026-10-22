using UnrealBuildTool;
using System.Collections.Generic;
public class KeralaRacingTarget : TargetRules {
 public KeralaRacingTarget(TargetInfo Target) : base(Target) {
  Type=TargetType.Game; DefaultBuildSettings=BuildSettingsVersion.V5;
  ExtraModuleNames.Add("KeralaRacing");
 }
}
