using UnrealBuildTool;
public class KeralaRacing : ModuleRules {
 public KeralaRacing(ReadOnlyTargetRules Target) : base(Target) {
  PCHUsage=PCHUsageMode.UseExplicitOrSharedPCHs;
  PublicDependencyModuleNames.AddRange(new string[]{"Core","CoreUObject","Engine","InputCore"});
 }
}
