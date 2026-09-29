// Copyright Southern Spear. All Rights Reserved.

#include "SSCasualtySettings.h"

SSCasualty::FTuning USSCasualtySettings::ToTuning() const
{
	SSCasualty::FTuning T;
	T.MaxHealth = MaxHealth;
	T.HeadMultiplier = HeadMultiplier;
	T.TorsoMultiplier = TorsoMultiplier;
	T.ArmMultiplier = ArmMultiplier;
	T.LegMultiplier = LegMultiplier;
	T.HeadBleedPerDamage = HeadBleedPerDamage;
	T.TorsoBleedPerDamage = TorsoBleedPerDamage;
	T.ArmBleedPerDamage = ArmBleedPerDamage;
	T.LegBleedPerDamage = LegBleedPerDamage;
	T.MaxBleed = MaxBleed;
	T.BleedOutSeconds = BleedOutSeconds;
	T.DressingSelfSeconds = DressingSelfSeconds;
	T.DressingTeammateSeconds = DressingTeammateSeconds;
	T.StabiliseTeammateSeconds = StabiliseTeammateSeconds;
	T.StabiliseMedicSeconds = StabiliseMedicSeconds;
	T.TreatMedicSeconds = TreatMedicSeconds;
	T.KitSelfTreatSeconds = KitSelfTreatSeconds;
	T.StabiliseTeammateHealth = StabiliseTeammateHealth;
	T.StabiliseTeammateBleed = StabiliseTeammateBleed;
	T.StabiliseMedicHealth = StabiliseMedicHealth;
	T.TreatMedicHealth = TreatMedicHealth;
	T.KitSelfTreatHealth = KitSelfTreatHealth;
	T.DressingsCarried = DressingsCarried;
	T.MedicDressingsCarried = MedicDressingsCarried;
	T.KitCharges = KitCharges;
	T.KitLifetimeSeconds = KitLifetimeSeconds;
	T.KitRadiusCm = KitRadiusCm;
	return T;
}

SSCasualty::EZone USSCasualtySettings::ZoneForBone(FName BoneName) const
{
	const FString Bone = BoneName.ToString();
	const auto Matches = [&Bone](const TArray<FString>& Fragments)
	{
		for (const FString& Fragment : Fragments)
		{
			if (!Fragment.IsEmpty() && Bone.Contains(Fragment, ESearchCase::IgnoreCase))
			{
				return true;
			}
		}
		return false;
	};
	// Head first: "neck" and "head" must not fall through to an arm match on "clavicle"-style names.
	if (Matches(HeadBones)) return SSCasualty::EZone::Head;
	if (Matches(ArmBones)) return SSCasualty::EZone::Arm;
	if (Matches(LegBones)) return SSCasualty::EZone::Leg;
	return SSCasualty::EZone::Torso;
}
